from typing import Iterable, List, Dict, Any, Optional
from datetime import datetime
import hashlib
import re

from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import ApiError, TransportError, NotFoundError
from app.config import settings
import logging

logger = logging.getLogger(__name__)

LEADING_COMMENT_RE = re.compile(r"^/\*.*?\*/\s*", re.DOTALL)
WHITESPACE_RE = re.compile(r"\s+")
SINGLE_QUOTED_STRING_RE = re.compile(r"'(?:''|[^'])*'")
UUID_LITERAL_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b"
)
NUMERIC_LITERAL_RE = re.compile(r"(?<![\w])[-+]?\d+(?:\.\d+)?(?![\w])")
IN_LIST_RE = re.compile(r"\bIN\s*\((?:\s*\?\s*,)*\s*\?\s*\)", re.IGNORECASE)
LIMIT_PAIR_RE = re.compile(r"\bLIMIT\s+\?\s*,\s*\?", re.IGNORECASE)
COMPARISON_OPERATOR_RE = re.compile(r"\s*(<>|!=|>=|<=|=|>|<)\s*")


class ESService:
    """Elasticsearch查询服务"""
    CLUSTER_SCAN_LIMIT = 2000
    CLUSTER_BATCH_SIZE = 200
    CLUSTER_REQUEST_TIMEOUT_SECONDS = 8
    CLUSTER_SORT_ALIASES = {
        "cluster_count": "cluster_count",
        "share": "cluster_count",
        "avg_query_time_ms": "avg_query_time_ms",
        "latest_timestamp": "latest_timestamp",
        "dbname": "dbname",
        "type": "type",
        "dbuser": "dbuser",
        "upstream_addr": "upstream_addr",
    }
    
    def __init__(self):
        """初始化ES客户端"""
        es_config = {
            "hosts": [settings.get_es_url()],
            "verify_certs": settings.es_use_ssl,
        }
        
        if settings.es_username and settings.es_password:
            es_config["basic_auth"] = (settings.es_username, settings.es_password)
        
        self.client = Elasticsearch(**es_config)
        self.index_pattern = settings.es_index_pattern

    @staticmethod
    def normalize_sql_template(sql: Optional[str]) -> Optional[str]:
        sql_text = (sql or "").strip()
        while True:
            stripped = LEADING_COMMENT_RE.sub("", sql_text)
            if stripped == sql_text:
                break
            sql_text = stripped.strip()

        sql_text = WHITESPACE_RE.sub(" ", sql_text).strip().rstrip(";")
        if not sql_text:
            return None

        sql_text = SINGLE_QUOTED_STRING_RE.sub("?", sql_text)
        sql_text = UUID_LITERAL_RE.sub("?", sql_text)
        sql_text = NUMERIC_LITERAL_RE.sub("?", sql_text)
        sql_text = IN_LIST_RE.sub("IN (?)", sql_text)
        sql_text = LIMIT_PAIR_RE.sub("LIMIT ?", sql_text)
        sql_text = COMPARISON_OPERATOR_RE.sub(r" \1 ", sql_text)
        sql_text = re.sub(r"\(\s*\?\s*(?:,\s*\?\s*)+\)", "(?)", sql_text)
        sql_text = WHITESPACE_RE.sub(" ", sql_text).strip()
        return sql_text.upper()

    @staticmethod
    def _parse_query_time_ms(query_time_str: Optional[str]) -> Optional[float]:
        if query_time_str in (None, ""):
            return None
        try:
            return round(float(query_time_str) * 1000, 2)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _cluster_id(record_type: Optional[str], dbname: Optional[str], upstream_addr: Optional[str], template_sql: str) -> str:
        source = "|".join(
            [
                (record_type or "").lower(),
                dbname or "",
                upstream_addr or "",
                template_sql,
            ]
        )
        return hashlib.sha1(source.encode("utf-8")).hexdigest()

    @classmethod
    def check_connection(cls) -> tuple[bool, str]:
        try:
            client = Elasticsearch(
                hosts=[settings.get_es_url()],
                verify_certs=settings.es_use_ssl,
                basic_auth=(settings.es_username, settings.es_password)
                if settings.es_username and settings.es_password
                else None,
            )
            if client.ping():
                return True, "ok"
            return False, "ping failed"
        except Exception as exc:  # pragma: no cover - 运行时诊断逻辑
            return False, str(exc)
    
    def build_query(
        self,
        query_time_min: Optional[float] = None,
        query_time_max: Optional[float] = None,
        timestamp_start: Optional[str] = None,
        timestamp_end: Optional[str] = None,
        keyword: Optional[str] = None,
        dbname: Optional[str] = None,
        dbuser: Optional[str] = None,
        type: Optional[str] = None,
        upstream_addr: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        构建ES查询DSL
        """
        must_clauses = []
        must_not_clauses = []
        
        # 默认过滤：只保留 cmd 为 'query' 的记录（使用 keyword 子字段，避免分词干扰）
        must_clauses.append({
            "term": {
                "cmd.keyword": "query"
            }
        })

        # 执行耗时范围查询
        # query_time在ES中可能是字符串类型，需要使用script查询进行数值比较
        if query_time_min is not None or query_time_max is not None:
            script_params = {}
            conditions = []

            if query_time_min is not None:
                script_params["min"] = query_time_min
                conditions.append("queryTime >= params.min")
            if query_time_max is not None:
                script_params["max"] = query_time_max
                conditions.append("queryTime <= params.max")

            script_source = """
                double queryTime = 0.0;
                if (doc.containsKey('query_time') && !doc['query_time'].empty) {
                    try {
                        queryTime = Double.parseDouble(doc['query_time'].value.toString());
                    } catch (Exception ignored) {
                        queryTime = 0.0;
                    }
                }
                return %s;
            """ % " && ".join(conditions)
            
            must_clauses.append({
                "script": {
                    "script": {
                        "source": script_source,
                        "lang": "painless",
                        "params": script_params
                    }
                }
            })
        
        # 记录时间范围查询
        if timestamp_start or timestamp_end:
            timestamp_range = {}
            if timestamp_start:
                timestamp_range["gte"] = self._parse_timestamp(timestamp_start)
            if timestamp_end:
                timestamp_range["lte"] = self._parse_timestamp(timestamp_end)
            
            must_clauses.append({
                "range": {
                    "timestamp": timestamp_range
                }
            })
        
        # 关键词模糊匹配（匹配query字段）
        if keyword:
            must_clauses.append({
                "query_string": {
                    "query": f"*{keyword}*",
                    "fields": ["query"],
                    "default_operator": "AND"
                }
            })
        
        # 数据库名精确匹配
        if dbname:
            must_clauses.append(self._build_exact_match_clause("dbname", dbname))
        
        # 数据库用户精确匹配
        if dbuser:
            must_clauses.append(self._build_exact_match_clause("dbuser", dbuser))
        
        # 数据库类型精确匹配
        if type:
            must_clauses.append(self._build_exact_match_clause("type", type))
        
        # 数据库地址精确匹配
        if upstream_addr:
            must_clauses.append(self._build_exact_match_clause("upstream_addr", upstream_addr))
        
        # 构建bool查询
        bool_query = {}
        
        if must_clauses:
            bool_query["must"] = must_clauses
        
        if must_not_clauses:
            bool_query["must_not"] = must_not_clauses
        
        if bool_query:
            query = {"bool": bool_query}
        else:
            query = {"match_all": {}}
        
        return query

    def _build_exact_match_clause(self, field: str, value: str) -> Dict[str, Any]:
        """
        为 text+keyword 混合字段构造兼容查询。

        - 优先命中 `{field}.keyword`，保留真正的精确匹配
        - 同时回退到 `match_phrase`，兼容 text 字段的大小写/分词差异
        """
        return {
            "bool": {
                "should": [
                    {"term": {f"{field}.keyword": value}},
                    {"match_phrase": {field: value}},
                ],
                "minimum_should_match": 1,
            }
        }
    
    def _parse_timestamp(self, timestamp_str: str) -> int:
        """
        解析时间戳字符串
        支持ISO格式和时间戳（毫秒）
        """
        try:
            # 尝试解析为时间戳（毫秒）
            if timestamp_str.isdigit():
                return int(timestamp_str)
            
            # 尝试解析为ISO格式
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            return int(dt.timestamp() * 1000)
        except Exception as e:
            logger.warning(f"Failed to parse timestamp {timestamp_str}: {e}")
            # 如果解析失败，返回当前时间戳
            return int(datetime.now().timestamp() * 1000)
    
    def _is_slow_sql(self, query_time_str: Optional[str]) -> Optional[bool]:
        """
        判断是否为慢SQL
        执行时间>1秒的为慢SQL
        
        Args:
            query_time_str: query_time字段值（可能是字符串格式）
            
        Returns:
            True表示慢SQL，False表示非慢SQL，None表示无法判断
        """
        if not query_time_str:
            return None
        
        try:
            # 尝试将query_time转换为浮点数（秒）
            query_time = float(query_time_str)
            # 判断是否大于1秒
            return query_time > 1
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to parse query_time '{query_time_str}': {e}")
            return None

    def get_record_by_id(self, index: str, record_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.client.get(index=index, id=record_id)
        except NotFoundError:
            return None
        except (ApiError, TransportError) as e:
            logger.error(f"Elasticsearch get record error: {e}")
            return None

        source = response.get("_source", {})
        return {
            "id": response.get("_id"),
            "index": response.get("_index"),
            "timestamp": source.get("timestamp"),
            "dbname": source.get("dbname"),
            "dbuser": source.get("dbuser"),
            "db_type": source.get("type"),
            "workgroup_name": source.get("workgroup_name"),
            "query": source.get("query"),
            "query_time": source.get("query_time"),
            "client_ip": source.get("client_ip"),
            "upstream_addr": source.get("upstream_addr"),
        }

    def get_sql_observability(
        self,
        sql: str,
        dbname: Optional[str] = None,
        db_type: Optional[str] = None,
        upstream_addr: Optional[str] = None,
    ) -> Dict[str, Any]:
        must_clauses: list[dict[str, Any]] = [
            {"term": {"cmd.keyword": "query"}},
            {"match_phrase": {"query": sql}},
        ]

        if dbname:
            must_clauses.append(self._build_exact_match_clause("dbname", dbname))
        if db_type:
            must_clauses.append(self._build_exact_match_clause("type", db_type))
        if upstream_addr:
            must_clauses.append(self._build_exact_match_clause("upstream_addr", upstream_addr))

        body = {
            "query": {"bool": {"must": must_clauses}},
            "size": 0,
            "track_total_hits": True,
            "aggs": {
                "avg_query_time": {
                    "avg": {
                        "script": {
                            "lang": "painless",
                            "source": """
                                if (doc.containsKey('query_time') && !doc['query_time'].empty) {
                                    try {
                                        return Double.parseDouble(doc['query_time'].value.toString());
                                    } catch (Exception ignored) {
                                        return 0.0;
                                    }
                                }
                                return 0.0;
                            """,
                        }
                    }
                },
                "min_query_time": {
                    "min": {
                        "script": {
                            "lang": "painless",
                            "source": """
                                if (doc.containsKey('query_time') && !doc['query_time'].empty) {
                                    try {
                                        return Double.parseDouble(doc['query_time'].value.toString());
                                    } catch (Exception ignored) {
                                        return null;
                                    }
                                }
                                return null;
                            """,
                        }
                    }
                },
                "max_query_time": {
                    "max": {
                        "script": {
                            "lang": "painless",
                            "source": """
                                if (doc.containsKey('query_time') && !doc['query_time'].empty) {
                                    try {
                                        return Double.parseDouble(doc['query_time'].value.toString());
                                    } catch (Exception ignored) {
                                        return 0.0;
                                    }
                                }
                                return 0.0;
                            """,
                        }
                    }
                },
            },
        }

        try:
            response = self.client.search(index=self.index_pattern, body=body)
            total_hits = response["hits"]["total"]["value"] if isinstance(response["hits"]["total"], dict) else response["hits"]["total"]
            return {
                "exact_match_count": total_hits,
                "cluster_count": total_hits,
                "min_query_time_ms": round(float(response["aggregations"]["min_query_time"]["value"] or 0) * 1000, 2)
                if response["aggregations"]["min_query_time"]["value"] is not None
                else None,
                "avg_query_time_ms": round(float(response["aggregations"]["avg_query_time"]["value"] or 0) * 1000, 2),
                "max_query_time_ms": round(float(response["aggregations"]["max_query_time"]["value"] or 0) * 1000, 2),
            }
        except Exception as exc:
            logger.warning("Failed to aggregate SQL observability: %s", exc)
            return {
                "exact_match_count": 0,
                "cluster_count": 0,
                "min_query_time_ms": None,
                "avg_query_time_ms": 0.0,
                "max_query_time_ms": 0.0,
                "error": str(exc),
            }

    def _serialize_hit(self, hit: Dict[str, Any]) -> Dict[str, Any]:
        source = hit["_source"]
        query_time_str = source.get("query_time")
        return {
            "id": hit.get("_id"),
            "timestamp": source.get("timestamp", 0),
            "upstream_addr": source.get("upstream_addr"),
            "client_ip": source.get("client_ip"),
            "cmd": source.get("cmd"),
            "query": source.get("query"),
            "dbname": source.get("dbname"),
            "dbuser": source.get("dbuser"),
            "type": source.get("type"),
            "workgroup_name": source.get("workgroup_name"),
            "client_port": source.get("client_port"),
            "query_time": query_time_str,
            "resplen": source.get("resplen"),
            "rows_num": source.get("rows_num"),
            "session_time": source.get("session_time"),
            "upstream_name": source.get("upstream_name"),
            "realtime": source.get("realtime"),
            "fields_num": source.get("fields_num"),
            "status": source.get("status"),
            "workgroup_id": source.get("workgroup_id"),
            "dbtable": source.get("dbtable"),
            "is_slow_sql": self._is_slow_sql(query_time_str),
        }

    def iter_filtered_records(
        self,
        query_time_min: Optional[float] = None,
        query_time_max: Optional[float] = None,
        timestamp_start: Optional[str] = None,
        timestamp_end: Optional[str] = None,
        keyword: Optional[str] = None,
        dbname: Optional[str] = None,
        dbuser: Optional[str] = None,
        type: Optional[str] = None,
        upstream_addr: Optional[str] = None,
    ) -> Iterable[Dict[str, Any]]:
        query = self.build_query(
            query_time_min=query_time_min,
            query_time_max=query_time_max,
            timestamp_start=timestamp_start,
            timestamp_end=timestamp_end,
            keyword=keyword,
            dbname=dbname,
            dbuser=dbuser,
            type=type,
            upstream_addr=upstream_addr,
        )
        source_fields = [
            "timestamp",
            "upstream_addr",
            "client_ip",
            "cmd",
            "query",
            "dbname",
            "dbuser",
            "type",
            "workgroup_name",
            "client_port",
            "query_time",
            "status",
        ]

        for hit in helpers.scan(
            self.client,
            index=self.index_pattern,
            query={"query": query, "_source": source_fields},
            preserve_order=False,
            scroll="2m",
        ):
            yield self._serialize_hit(hit)

    def search_clusters(
        self,
        query_time_min: Optional[float] = None,
        query_time_max: Optional[float] = None,
        timestamp_start: Optional[str] = None,
        timestamp_end: Optional[str] = None,
        keyword: Optional[str] = None,
        dbname: Optional[str] = None,
        dbuser: Optional[str] = None,
        type: Optional[str] = None,
        upstream_addr: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        records, total_record_count, truncated = self._fetch_recent_filtered_records_for_clustering(
            query_time_min=query_time_min,
            query_time_max=query_time_max,
            timestamp_start=timestamp_start,
            timestamp_end=timestamp_end,
            keyword=keyword,
            dbname=dbname,
            dbuser=dbuser,
            type=type,
            upstream_addr=upstream_addr,
            max_records=self.CLUSTER_SCAN_LIMIT,
            batch_size=self.CLUSTER_BATCH_SIZE,
        )
        return self._cluster_records(
            records=records,
            total_record_count=total_record_count,
            truncated=truncated,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
        )

    def _fetch_recent_filtered_records_for_clustering(
        self,
        query_time_min: Optional[float] = None,
        query_time_max: Optional[float] = None,
        timestamp_start: Optional[str] = None,
        timestamp_end: Optional[str] = None,
        keyword: Optional[str] = None,
        dbname: Optional[str] = None,
        dbuser: Optional[str] = None,
        type: Optional[str] = None,
        upstream_addr: Optional[str] = None,
        max_records: int = CLUSTER_SCAN_LIMIT,
        batch_size: int = CLUSTER_BATCH_SIZE,
    ) -> tuple[List[Dict[str, Any]], int, bool]:
        query = self.build_query(
            query_time_min=query_time_min,
            query_time_max=query_time_max,
            timestamp_start=timestamp_start,
            timestamp_end=timestamp_end,
            keyword=keyword,
            dbname=dbname,
            dbuser=dbuser,
            type=type,
            upstream_addr=upstream_addr,
        )
        source_fields = [
            "timestamp",
            "upstream_addr",
            "client_ip",
            "cmd",
            "query",
            "dbname",
            "dbuser",
            "type",
            "workgroup_name",
            "client_port",
            "query_time",
            "status",
        ]
        normalized_batch_size = max(1, min(batch_size, max_records))
        collected_hits: List[Dict[str, Any]] = []
        offset = 0
        total_hits = 0

        while offset < max_records:
            search_body = {
                "query": query,
                "from": offset,
                "size": min(normalized_batch_size, max_records - offset),
                "sort": [{"timestamp": {"order": "desc"}}],
                "track_total_hits": True,
                "_source": source_fields,
            }
            response = self.client.search(
                index=self.index_pattern,
                body=search_body,
                request_timeout=self.CLUSTER_REQUEST_TIMEOUT_SECONDS,
            )
            hits_total = response["hits"]["total"]
            total_hits = hits_total["value"] if isinstance(hits_total, dict) else hits_total
            hits = response["hits"]["hits"]
            if not hits:
                break

            collected_hits.extend(self._serialize_hit(hit) for hit in hits)
            offset += len(hits)

            if len(hits) < search_body["size"]:
                break

        truncated = total_hits > len(collected_hits)
        if truncated:
            logger.warning(
                "Cluster search truncated matched records from %s to %s for stability",
                total_hits,
                len(collected_hits),
            )
        return collected_hits, total_hits, truncated

    @classmethod
    def _normalize_cluster_sort(
        cls,
        sort_by: Optional[str],
        sort_order: Optional[str],
    ) -> tuple[str, str]:
        normalized_sort_by = cls.CLUSTER_SORT_ALIASES.get((sort_by or "").strip(), "cluster_count")
        normalized_sort_order = "asc" if (sort_order or "").lower() == "asc" else "desc"
        return normalized_sort_by, normalized_sort_order

    @staticmethod
    def _cluster_sort_value(item: Dict[str, Any], sort_by: str) -> Any:
        value = item.get(sort_by)
        if isinstance(value, str):
            return value.lower()
        if value is None:
            return float("-inf")
        return value

    @classmethod
    def _cluster_records(
        cls,
        records: List[Dict[str, Any]],
        total_record_count: Optional[int] = None,
        truncated: bool = False,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        scanned_record_count = len(records)
        if total_record_count is None:
            total_record_count = scanned_record_count
        clusters: Dict[str, Dict[str, Any]] = {}

        for record in records:
            template_sql = cls.normalize_sql_template(record.get("query"))
            if not template_sql:
                continue

            cluster_id = cls._cluster_id(
                record_type=record.get("type"),
                dbname=record.get("dbname"),
                upstream_addr=record.get("upstream_addr"),
                template_sql=template_sql,
            )
            query_time_ms = cls._parse_query_time_ms(record.get("query_time"))
            timestamp = int(record.get("timestamp") or 0)

            if cluster_id not in clusters:
                clusters[cluster_id] = {
                    "cluster_id": cluster_id,
                    "template_sql": template_sql,
                    "sample_sql": record.get("query") or template_sql,
                    "dbname": record.get("dbname"),
                    "dbuser": record.get("dbuser"),
                    "type": record.get("type"),
                    "upstream_addr": record.get("upstream_addr"),
                    "cluster_count": 0,
                    "first_timestamp": timestamp,
                    "min_query_time_ms": None,
                    "avg_query_time_ms": None,
                    "max_query_time_ms": None,
                    "latest_timestamp": timestamp,
                    "is_slow_sql": False,
                    "_sum_query_time_ms": 0.0,
                    "_valid_query_time_count": 0,
                }

            cluster = clusters[cluster_id]
            cluster["cluster_count"] += 1
            if cluster["first_timestamp"] == 0 or (timestamp and timestamp < cluster["first_timestamp"]):
                cluster["first_timestamp"] = timestamp
            if timestamp >= cluster["latest_timestamp"]:
                cluster["latest_timestamp"] = timestamp
                cluster["sample_sql"] = record.get("query") or template_sql

            if query_time_ms is not None:
                cluster["_sum_query_time_ms"] += query_time_ms
                cluster["_valid_query_time_count"] += 1
                cluster["min_query_time_ms"] = (
                    query_time_ms
                    if cluster["min_query_time_ms"] is None
                    else min(cluster["min_query_time_ms"], query_time_ms)
                )
                cluster["max_query_time_ms"] = (
                    query_time_ms
                    if cluster["max_query_time_ms"] is None
                    else max(cluster["max_query_time_ms"], query_time_ms)
                )
                cluster["is_slow_sql"] = bool(cluster["is_slow_sql"] or query_time_ms > 1000)

        clustered_items: List[Dict[str, Any]] = []
        for cluster in clusters.values():
            valid_count = cluster.pop("_valid_query_time_count")
            sum_query_time_ms = cluster.pop("_sum_query_time_ms")
            cluster["avg_query_time_ms"] = round(sum_query_time_ms / valid_count, 2) if valid_count else None
            clustered_items.append(cluster)

        normalized_sort_by, normalized_sort_order = cls._normalize_cluster_sort(sort_by, sort_order)
        reverse = normalized_sort_order == "desc"
        clustered_items.sort(
            key=lambda item: (
                cls._cluster_sort_value(item, normalized_sort_by),
                item.get("latest_timestamp", 0),
                item.get("cluster_id", ""),
            ),
            reverse=reverse,
        )

        total = len(clustered_items)
        from_index = (page - 1) * page_size
        paged_items = clustered_items[from_index: from_index + page_size]

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_record_count": total_record_count,
            "scanned_record_count": scanned_record_count,
            "truncated": truncated,
            "sort_by": normalized_sort_by,
            "sort_order": normalized_sort_order,
            "items": paged_items,
        }
    
    def search(
        self,
        query_time_min: Optional[float] = None,
        query_time_max: Optional[float] = None,
        timestamp_start: Optional[str] = None,
        timestamp_end: Optional[str] = None,
        keyword: Optional[str] = None,
        dbname: Optional[str] = None,
        dbuser: Optional[str] = None,
        type: Optional[str] = None,
        upstream_addr: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        执行ES查询
        """
        try:
            query = self.build_query(
                query_time_min=query_time_min,
                query_time_max=query_time_max,
                timestamp_start=timestamp_start,
                timestamp_end=timestamp_end,
                keyword=keyword,
                dbname=dbname,
                dbuser=dbuser,
                type=type,
                upstream_addr=upstream_addr,
            )
            
            from_index = (page - 1) * page_size
            
            search_body = {
                "query": query,
                "from": from_index,
                "size": page_size,
                "sort": [{"timestamp": {"order": "desc"}}],
                "track_total_hits": True,
            }
            
            response = self.client.search(
                index=self.index_pattern,
                body=search_body
            )
            
            total = response["hits"]["total"]["value"] if isinstance(
                response["hits"]["total"], dict
            ) else response["hits"]["total"]
            
            hits = response["hits"]["hits"]
            items = []
            
            for hit in hits:
                items.append(self._serialize_hit(hit))
            
            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": items
            }
            
        except NotFoundError:
            # 索引不存在时返回空结果
            return {
                "total": 0,
                "page": page,
                "page_size": page_size,
                "items": []
            }
        except (ApiError, TransportError) as e:
            logger.error(f"Elasticsearch query error: {e}")
            raise Exception(f"ES查询失败: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in ES search: {e}")
            raise Exception(f"查询失败: {str(e)}")

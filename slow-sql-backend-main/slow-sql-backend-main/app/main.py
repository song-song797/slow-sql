import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.staticfiles import StaticFiles
from app.routers import data_sources, es_query, database_info, sql_analysis
from app.database import init_database, check_database_connection
from app.services.es_service import ESService
from app.services.report_service import ReportService
import logging
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# 创建FastAPI应用，禁用默认的docs和redoc，我们将自定义它们
app = FastAPI(
    title="Slow SQL Analysis API",
    description="用于根据SQL在测试环境的执行情况，结合生产环境表结构和总行数等信息分析慢SQL的API服务",
    version="1.0.0",
    docs_url=None,  # 禁用默认的docs，使用自定义的
    redoc_url=None,  # 禁用默认的redoc，使用自定义的
)

# 配置本地 Swagger UI 静态资源路径
# 静态文件应该放在项目根目录的 static/swagger-ui/ 目录下
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static", "swagger-ui")
REPORTS_DIR = os.path.join(BASE_DIR, "static", "reports")
swagger_ui_path = None

os.makedirs(REPORTS_DIR, exist_ok=True)
app.mount("/static/reports", StaticFiles(directory=REPORTS_DIR), name="reports")

# 检查本地静态文件目录是否存在
if os.path.exists(STATIC_DIR):
    bundle_file = os.path.join(STATIC_DIR, "swagger-ui-bundle.js")
    if os.path.exists(bundle_file):
        swagger_ui_path = STATIC_DIR
        # 挂载静态文件目录
        app.mount("/static/swagger-ui", StaticFiles(directory=STATIC_DIR), name="swagger-ui")
        logger.info(f"已配置本地 Swagger UI 资源路径: {swagger_ui_path}")
    else:
        logger.warning(f"在 {STATIC_DIR} 目录下未找到 swagger-ui-bundle.js 文件")
        logger.warning("请运行 download_swagger_ui.py 脚本下载静态文件，或手动下载到 static/swagger-ui/ 目录")
else:
    logger.warning(f"静态文件目录 {STATIC_DIR} 不存在")
    logger.warning("请运行 download_swagger_ui.py 脚本下载静态文件，或手动创建目录并下载文件")

if not swagger_ui_path:
    logger.warning("将尝试使用 CDN（可能在内网环境无法访问）")

# 自定义 Swagger UI，使用本地静态资源
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    if swagger_ui_path:
        # 使用本地静态资源
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=app.title + " - Swagger UI",
            swagger_js_url="/static/swagger-ui/swagger-ui-bundle.js",
            swagger_css_url="/static/swagger-ui/swagger-ui.css",
        )
    else:
        # 回退到默认（使用 CDN）
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=app.title + " - Swagger UI",
        )

# 自定义 ReDoc，使用本地静态资源
@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    if swagger_ui_path:
        # 使用本地静态资源
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=app.title + " - ReDoc",
            redoc_js_url="/static/swagger-ui/redoc.standalone.js",
        )
    else:
        # 回退到默认（使用 CDN）
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=app.title + " - ReDoc",
        )

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(es_query.router)
app.include_router(database_info.router)
app.include_router(data_sources.router)
app.include_router(sql_analysis.router)


async def _initialize_database_in_background() -> None:
    """后台初始化数据库表结构，避免启动期被慢数据库操作阻塞。"""
    try:
        await asyncio.to_thread(init_database)
        logger.info("数据库表结构初始化完成")
    except Exception as exc:  # pragma: no cover - 启动期容错
        logger.warning("数据库表结构初始化失败，应用继续启动: %s", exc)


@app.on_event("startup")
async def startup_event():
    """尝试初始化数据库表结构，但不阻塞应用启动。"""
    app.state.database_init_task = asyncio.create_task(_initialize_database_in_background())


@app.get("/", tags=["根路径"])
async def root():
    """根路径，返回API信息"""
    return {
        "message": "Slow SQL Analysis API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查接口"""
    return {"status": "healthy"}


@app.get("/ready", tags=["健康检查"])
async def readiness_check():
    """依赖就绪检查接口。"""
    async def run_thread_check(func, fallback_name: str) -> tuple[bool, str]:
        try:
            return await asyncio.wait_for(asyncio.to_thread(func), timeout=5)
        except asyncio.TimeoutError:
            return False, f"{fallback_name} timeout"
        except Exception as exc:  # pragma: no cover - 运行时诊断逻辑
            return False, str(exc)

    async def run_report_check() -> tuple[bool, str]:
        try:
            return await asyncio.wait_for(ReportService().check_provider_health(), timeout=5)
        except asyncio.TimeoutError:
            return False, "report_provider timeout"
        except Exception as exc:  # pragma: no cover - 运行时诊断逻辑
            return False, str(exc)

    db_future = run_thread_check(check_database_connection, "database")
    es_future = run_thread_check(ESService.check_connection, "elasticsearch")
    report_future = run_report_check()

    db_ok, db_message = await db_future
    es_ok, es_message = await es_future
    report_ok, report_message = await report_future

    ready = db_ok and es_ok and report_ok
    return {
        "status": "ready" if ready else "degraded",
        "dependencies": {
            "database": {"ok": db_ok, "message": db_message},
            "elasticsearch": {"ok": es_ok, "message": es_message},
            "report_provider": {"ok": report_ok, "message": report_message},
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10800)

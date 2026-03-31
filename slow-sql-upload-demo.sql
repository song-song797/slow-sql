SELECT * FROM t_order WHERE user_id = 10001 ORDER BY create_time DESC LIMIT 20;

SELECT * FROM t_order WHERE status = 'PAID' ORDER BY update_time DESC LIMIT 100;

SELECT * FROM t_user WHERE phone = '13800138000';

SELECT * FROM t_pay_record WHERE merchant_id = 20001 AND pay_status = 'SUCCESS' ORDER BY pay_time DESC LIMIT 50;

SELECT o.* FROM t_order o LEFT JOIN t_order_item i ON o.id = i.order_id WHERE o.user_id = 10001 AND i.sku_id = 90001 ORDER BY o.create_time DESC LIMIT 30;

SELECT * FROM t_log WHERE request_path LIKE '%/api/order/%' AND create_time >= '2026-03-01 00:00:00' AND create_time < '2026-03-21 00:00:00';

SELECT * FROM t_inventory WHERE warehouse_id = 10 AND available_stock > 0 ORDER BY update_time DESC LIMIT 200;

SELECT user_id, COUNT(*) AS total_count FROM t_order GROUP BY user_id ORDER BY total_count DESC LIMIT 100;

SELECT * FROM t_message WHERE send_status = 0 AND retry_count < 5 ORDER BY create_time ASC LIMIT 500;

SELECT * FROM t_refund_record WHERE refund_status IN ('PROCESSING', 'SUCCESS') AND create_time >= '2026-03-01 00:00:00' ORDER BY create_time DESC LIMIT 100;

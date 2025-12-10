SELECT
    window_start,
    window_end,
    ARRAY_AGG(DISTINCT itemid) AS item_ids,
    COUNT(*) AS total_orders,
    SUM(orderAmount) AS total_amount
FROM TABLE (
    TUMBLE(TABLE sales_orders, DESCRIPTOR(`$rowtime`), INTERVAL '10' SECOND)
)
GROUP BY window_start, window_end
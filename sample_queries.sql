-- 1. 각 매장별 가장 많이 판매된 상위 20개 제품
SELECT
    s.store_name,
    p.product_name,
    SUM(si.quantity) AS total_quantity
FROM Sale sa
JOIN Store s ON sa.store_id = s.store_id
JOIN SaleItem si ON sa.sale_id = si.sale_id
JOIN Product p ON si.product_id = p.product_id
GROUP BY s.store_id, p.product_id
ORDER BY s.store_name, total_quantity DESC
LIMIT 20;


-- 2. 시·도별 가장 많이 판매된 상위 20개 제품
SELECT
    s.province,
    p.product_name,
    SUM(si.quantity) AS total_quantity
FROM Sale sa
JOIN Store s ON sa.store_id = s.store_id
JOIN SaleItem si ON sa.sale_id = si.sale_id
JOIN Product p ON si.product_id = p.product_id
GROUP BY s.province, p.product_id
ORDER BY s.province, total_quantity DESC
LIMIT 20;


-- 3. 판매 실적이 우수한 상위 5개 매장
SELECT
    s.store_name,
    s.province,
    s.city,
    SUM(sa.total_amount) AS total_sales,
    COUNT(sa.sale_id) AS sale_count
FROM Sale sa
JOIN Store s ON sa.store_id = s.store_id
GROUP BY s.store_id
ORDER BY total_sales DESC
LIMIT 5;


-- 4. 코카콜라보다 펩시콜라가 더 많이 판매된 매장의 수
WITH brand_sales AS (
    SELECT
        s.store_id,
        s.store_name,
        b.brand_name,
        SUM(si.quantity) AS total_quantity
    FROM Sale sa
    JOIN Store s ON sa.store_id = s.store_id
    JOIN SaleItem si ON sa.sale_id = si.sale_id
    JOIN Product p ON si.product_id = p.product_id
    JOIN Brand b ON p.brand_id = b.brand_id
    WHERE b.brand_name IN ('코카콜라', '펩시')
    GROUP BY s.store_id, b.brand_name
),
pivot_sales AS (
    SELECT
        store_id,
        store_name,
        SUM(CASE WHEN brand_name = '코카콜라' THEN total_quantity ELSE 0 END) AS coke_qty,
        SUM(CASE WHEN brand_name = '펩시' THEN total_quantity ELSE 0 END) AS pepsi_qty
    FROM brand_sales
    GROUP BY store_id, store_name
)
SELECT
    COUNT(*) AS pepsi_more_than_coke_store_count
FROM pivot_sales
WHERE pepsi_qty > coke_qty;


-- 5. 소비자가 우유와 함께 가장 많이 구매한 제품 상위 3개
SELECT
    p2.product_name,
    SUM(si2.quantity) AS together_quantity
FROM SaleItem si1
JOIN Product p1 ON si1.product_id = p1.product_id
JOIN SaleItem si2 ON si1.sale_id = si2.sale_id
JOIN Product p2 ON si2.product_id = p2.product_id
WHERE p1.product_name LIKE '%우유%'
  AND si2.product_id <> si1.product_id
GROUP BY p2.product_id
ORDER BY together_quantity DESC
LIMIT 3;


-- 6. 현재 재고가 재주문 기준 이하인 상품 조회
SELECT
    s.store_name,
    p.product_name,
    i.stock_quantity,
    i.reorder_level,
    i.reorder_quantity
FROM Inventory i
JOIN Store s ON i.store_id = s.store_id
JOIN Product p ON i.product_id = p.product_id
WHERE i.stock_quantity <= i.reorder_level
ORDER BY s.store_name, i.stock_quantity ASC;


-- 7. 공급업체별 미처리 발주 목록 조회
SELECT
    sup.supplier_name,
    po.po_id,
    st.store_name,
    po.order_datetime,
    po.status,
    po.fulfillment
FROM PurchaseOrder po
JOIN Supplier sup ON po.supplier_id = sup.supplier_id
JOIN Store st ON po.store_id = st.store_id
WHERE po.fulfillment = 'N'
ORDER BY po.order_datetime;
-- 1. 각 매장별 가장 많이 판매된 상위 20개 제품
WITH store_product_sales AS (
    SELECT
        s.store_id,
        s.store_name,
        p.product_id,
        p.product_name,
        SUM(si.quantity) AS total_quantity
    FROM Sale sa
    JOIN Store s ON sa.store_id = s.store_id
    JOIN SaleItem si ON sa.sale_id = si.sale_id
    JOIN Product p ON si.product_id = p.product_id
    GROUP BY s.store_id, p.product_id
),
ranked_sales AS (
    SELECT
        store_name,
        product_name,
        total_quantity,
        ROW_NUMBER() OVER (
            PARTITION BY store_id
            ORDER BY total_quantity DESC
        ) AS ranking
    FROM store_product_sales
)
SELECT
    store_name,
    ranking,
    product_name,
    total_quantity
FROM ranked_sales
WHERE ranking <= 20
ORDER BY store_name, ranking;


-- 2. 시·도별 가장 많이 판매된 상위 20개 제품
WITH region_product_sales AS (
    SELECT
        s.province,
        p.product_id,
        p.product_name,
        SUM(si.quantity) AS total_quantity
    FROM Sale sa
    JOIN Store s ON sa.store_id = s.store_id
    JOIN SaleItem si ON sa.sale_id = si.sale_id
    JOIN Product p ON si.product_id = p.product_id
    GROUP BY s.province, p.product_id
),
ranked_sales AS (
    SELECT
        province,
        product_name,
        total_quantity,
        ROW_NUMBER() OVER (
            PARTITION BY province
            ORDER BY total_quantity DESC
        ) AS ranking
    FROM region_product_sales
)
SELECT
    province,
    ranking,
    product_name,
    total_quantity
FROM ranked_sales
WHERE ranking <= 20
ORDER BY province, ranking;


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
    po.status
FROM PurchaseOrder po
JOIN Supplier sup ON po.supplier_id = sup.supplier_id
JOIN Store st ON po.store_id = st.store_id
WHERE po.status IN ('ORDERED', 'PARTIAL')
ORDER BY po.order_datetime;


-- 8. 발주별 상품 입고 현황 조회
SELECT
    po.po_id,
    po.status,
    st.store_name,
    sup.supplier_name,
    p.product_name,
    poi.order_quantity,
    COALESCE(SUM(sri.received_quantity), 0) AS received_quantity,
    poi.order_quantity - COALESCE(SUM(sri.received_quantity), 0) AS remaining_quantity
FROM PurchaseOrder po
JOIN Store st ON po.store_id = st.store_id
JOIN Supplier sup ON po.supplier_id = sup.supplier_id
JOIN PurchaseOrderItem poi ON po.po_id = poi.po_id
JOIN Product p ON poi.product_id = p.product_id
LEFT JOIN StockReceipt sr ON po.po_id = sr.po_id
LEFT JOIN StockReceiptItem sri
    ON sr.receipt_id = sri.receipt_id
   AND poi.product_id = sri.product_id
GROUP BY po.po_id, p.product_id
ORDER BY po.po_id, p.product_name;


-- 9. 특정 상품의 공급업체 및 공급 가격 조회
SELECT
    p.product_name,
    sup.supplier_name,
    sp.supply_price
FROM SupplierProduct sp
JOIN Supplier sup ON sp.supplier_id = sup.supplier_id
JOIN Product p ON sp.product_id = p.product_id
ORDER BY p.product_name, sp.supply_price;


-- 10. 상품별 하위 타입 정보 조회
SELECT
    p.product_id,
    p.product_name,
    b.brand_name,
    CASE
        WHEN fb.product_id IS NOT NULL THEN 'FoodBeverageProduct'
        WHEN dg.product_id IS NOT NULL THEN 'DailyGoodsProduct'
        WHEN hp.product_id IS NOT NULL THEN 'HealthProduct'
        ELSE 'GeneralProduct'
    END AS product_subclass,
    fb.expiration_date,
    dg.material,
    hp.dosage_form
FROM Product p
JOIN Brand b ON p.brand_id = b.brand_id
LEFT JOIN FoodBeverageProduct fb ON p.product_id = fb.product_id
LEFT JOIN DailyGoodsProduct dg ON p.product_id = dg.product_id
LEFT JOIN HealthProduct hp ON p.product_id = hp.product_id
ORDER BY p.product_id;


-- 11. 자동 재주문 발주 대상 상품 조회
SELECT
    s.store_name,
    p.product_name,
    i.stock_quantity,
    i.reorder_level,
    i.reorder_quantity,
    sup.supplier_name,
    sp.supply_price
FROM Inventory i
JOIN Store s ON i.store_id = s.store_id
JOIN Product p ON i.product_id = p.product_id
JOIN SupplierProduct sp ON i.product_id = sp.product_id
JOIN Supplier sup ON sp.supplier_id = sup.supplier_id
WHERE i.stock_quantity <= i.reorder_level
  AND sp.supply_price = (
      SELECT MIN(sp2.supply_price)
      FROM SupplierProduct sp2
      WHERE sp2.product_id = i.product_id
  )
ORDER BY s.store_name, sup.supplier_name, p.product_name;


-- 12. 공급업체별 취급 브랜드 조회
SELECT
    sup.supplier_name,
    b.brand_name
FROM SupplierBrand sb
JOIN Supplier sup ON sb.supplier_id = sup.supplier_id
JOIN Brand b ON sb.brand_id = b.brand_id
ORDER BY sup.supplier_name, b.brand_name;
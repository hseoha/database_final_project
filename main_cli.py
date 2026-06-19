import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_NAME = BASE_DIR / "emart24.db"


VALID_ORDER_STATUSES = ("ORDERED", "PARTIAL", "FULFILLED", "CANCELLED")


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def print_rows(rows, headers):
    if not rows:
        print("조회 결과가 없습니다.")
        return

    print("-" * 100)
    print(" | ".join(headers))
    print("-" * 100)

    for row in rows:
        print(" | ".join(str(value) if value is not None else "NULL" for value in row))

    print("-" * 100)


def customer_menu():
    while True:
        print("\n=== 소비자 메뉴 ===")
        print("1. 상품 검색")
        print("2. 상품 상세 조회")
        print("3. 상품 구매")
        print("4. 구매 내역 조회")
        print("0. 뒤로 가기")

        choice = input("메뉴를 선택하세요: ")

        if choice == "1":
            search_products()
        elif choice == "2":
            product_detail()
        elif choice == "3":
            buy_product()
        elif choice == "4":
            customer_purchase_history()
        elif choice == "0":
            break
        else:
            print("잘못된 입력입니다.")


def search_products():
    keyword = input("검색할 상품명 또는 브랜드명: ")

    conn = get_connection()
    cur = conn.cursor()

    query = """
    SELECT
        p.product_id,
        p.product_name,
        b.brand_name,
        p.specification,
        p.package_type,
        s.store_name,
        i.selling_price,
        i.stock_quantity
    FROM Product p
    JOIN Brand b ON p.brand_id = b.brand_id
    JOIN Inventory i ON p.product_id = i.product_id
    JOIN Store s ON i.store_id = s.store_id
    WHERE p.product_name LIKE ?
       OR b.brand_name LIKE ?
    ORDER BY p.product_name, s.store_name;
    """

    cur.execute(query, (f"%{keyword}%", f"%{keyword}%"))
    rows = cur.fetchall()
    conn.close()

    print_rows(
        rows,
        ["상품ID", "상품명", "브랜드", "규격", "포장", "매장", "가격", "재고"]
    )


def product_detail():
    product_id = input("상세 조회할 상품 ID: ")

    conn = get_connection()
    cur = conn.cursor()

    query = """
    SELECT
        p.product_id,
        p.product_name,
        p.barcode,
        b.brand_name,
        p.specification,
        p.package_type,
        GROUP_CONCAT(c.category_name, ', ') AS categories,
        CASE
            WHEN fb.product_id IS NOT NULL THEN 'FoodBeverageProduct'
            WHEN dg.product_id IS NOT NULL THEN 'DailyGoodsProduct'
            WHEN hp.product_id IS NOT NULL THEN 'HealthProduct'
            ELSE 'GeneralProduct'
        END AS product_subclass,
        fb.expiration_date,
        dg.material,
        hp.health_product_type
    FROM Product p
    JOIN Brand b ON p.brand_id = b.brand_id
    LEFT JOIN ProductCategory pc ON p.product_id = pc.product_id
    LEFT JOIN Category c ON pc.category_id = c.category_id
    LEFT JOIN FoodBeverageProduct fb ON p.product_id = fb.product_id
    LEFT JOIN DailyGoodsProduct dg ON p.product_id = dg.product_id
    LEFT JOIN HealthProduct hp ON p.product_id = hp.product_id
    WHERE p.product_id = ?
    GROUP BY p.product_id;
    """

    cur.execute(query, (product_id,))
    rows = cur.fetchall()

    stock_query = """
    SELECT
        s.store_name,
        i.selling_price,
        i.stock_quantity
    FROM Inventory i
    JOIN Store s ON i.store_id = s.store_id
    WHERE i.product_id = ?
    ORDER BY s.store_name;
    """

    cur.execute(stock_query, (product_id,))
    stock_rows = cur.fetchall()
    conn.close()

    print("\n[상품 기본 정보]")
    print_rows(
        rows,
        ["상품ID", "상품명", "바코드", "브랜드", "규격", "포장", "분류", "하위타입", "유통기한", "재질", "건강용품유형"]
    )

    print("\n[매장별 가격 및 재고]")
    print_rows(
        stock_rows,
        ["매장명", "판매가격", "재고수량"]
    )


def buy_product():
    try:
        store_id = int(input("구매 매장 ID: "))
        product_id = int(input("구매 상품 ID: "))
        quantity = int(input("구매 수량: "))
        customer_input = input("회원 고객 ID 입력, 비회원이면 Enter: ").strip()
        customer_id = int(customer_input) if customer_input else None

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT stock_quantity, selling_price
            FROM Inventory
            WHERE store_id = ? AND product_id = ?;
            """,
            (store_id, product_id)
        )
        inventory = cur.fetchone()

        if inventory is None:
            print("해당 매장에 해당 상품 재고 정보가 없습니다.")
            conn.close()
            return

        stock_quantity, unit_price = inventory

        if stock_quantity < quantity:
            print("재고가 부족합니다.")
            conn.close()
            return

        total_amount = unit_price * quantity
        sale_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cur.execute(
            """
            INSERT INTO Sale (sale_datetime, total_amount, store_id, customer_id)
            VALUES (?, ?, ?, ?);
            """,
            (sale_datetime, total_amount, store_id, customer_id)
        )

        sale_id = cur.lastrowid

        cur.execute(
            """
            INSERT INTO SaleItem (sale_id, product_id, quantity, unit_price, discount_amount)
            VALUES (?, ?, ?, ?, 0);
            """,
            (sale_id, product_id, quantity, unit_price)
        )

        cur.execute(
            """
            UPDATE Inventory
            SET stock_quantity = stock_quantity - ?,
                last_updated = ?
            WHERE store_id = ? AND product_id = ?;
            """,
            (quantity, sale_datetime, store_id, product_id)
        )

        conn.commit()
        conn.close()

        print(f"구매 완료! 판매번호: {sale_id}, 총 결제 금액: {total_amount}원")

    except ValueError:
        print("숫자를 입력해야 하는 항목이 있습니다.")
    except sqlite3.IntegrityError as error:
        print(f"구매 처리 중 데이터 무결성 오류가 발생했습니다: {error}")


def customer_purchase_history():
    try:
        customer_id = int(input("조회할 고객 ID: "))

        conn = get_connection()
        cur = conn.cursor()

        query = """
        SELECT
            sa.sale_id,
            sa.sale_datetime,
            st.store_name,
            p.product_name,
            si.quantity,
            si.unit_price,
            sa.total_amount
        FROM Sale sa
        JOIN Store st ON sa.store_id = st.store_id
        JOIN SaleItem si ON sa.sale_id = si.sale_id
        JOIN Product p ON si.product_id = p.product_id
        WHERE sa.customer_id = ?
        ORDER BY sa.sale_datetime DESC;
        """

        cur.execute(query, (customer_id,))
        rows = cur.fetchall()
        conn.close()

        print_rows(
            rows,
            ["판매ID", "구매일시", "매장", "상품명", "수량", "단가", "총액"]
        )

    except ValueError:
        print("고객 ID는 숫자로 입력해야 합니다.")


def manager_menu():
    while True:
        print("\n=== 매장 관리자 메뉴 ===")
        print("1. 매장별 재고 조회")
        print("2. 재고 부족 상품 조회")
        print("3. 재고 수량 및 판매 가격 수정")
        print("4. 발주 요청 생성")
        print("5. 자동 재주문 발주 생성")
        print("0. 뒤로 가기")

        choice = input("메뉴를 선택하세요: ")

        if choice == "1":
            store_inventory()
        elif choice == "2":
            low_stock_products()
        elif choice == "3":
            update_inventory()
        elif choice == "4":
            create_purchase_order()
        elif choice == "5":
            auto_reorder()
        elif choice == "0":
            break
        else:
            print("잘못된 입력입니다.")


def store_inventory():
    try:
        store_id = int(input("조회할 매장 ID: "))

        conn = get_connection()
        cur = conn.cursor()

        query = """
        SELECT
            s.store_name,
            p.product_id,
            p.product_name,
            b.brand_name,
            i.stock_quantity,
            i.selling_price,
            i.reorder_level,
            i.reorder_quantity,
            i.last_updated
        FROM Inventory i
        JOIN Store s ON i.store_id = s.store_id
        JOIN Product p ON i.product_id = p.product_id
        JOIN Brand b ON p.brand_id = b.brand_id
        WHERE i.store_id = ?
        ORDER BY p.product_name;
        """

        cur.execute(query, (store_id,))
        rows = cur.fetchall()
        conn.close()

        print_rows(
            rows,
            ["매장", "상품ID", "상품명", "브랜드", "재고", "가격", "재주문기준", "재주문수량", "수정시각"]
        )

    except ValueError:
        print("매장 ID는 숫자로 입력해야 합니다.")


def low_stock_products():
    conn = get_connection()
    cur = conn.cursor()

    query = """
    SELECT
        s.store_id,
        s.store_name,
        p.product_id,
        p.product_name,
        i.stock_quantity,
        i.reorder_level,
        i.reorder_quantity
    FROM Inventory i
    JOIN Store s ON i.store_id = s.store_id
    JOIN Product p ON i.product_id = p.product_id
    WHERE i.stock_quantity <= i.reorder_level
    ORDER BY s.store_name, i.stock_quantity;
    """

    cur.execute(query)
    rows = cur.fetchall()
    conn.close()

    print_rows(
        rows,
        ["매장ID", "매장명", "상품ID", "상품명", "현재재고", "재주문기준", "재주문수량"]
    )


def update_inventory():
    try:
        store_id = int(input("수정할 매장 ID: "))
        product_id = int(input("수정할 상품 ID: "))
        stock_quantity = int(input("새 재고 수량: "))
        selling_price = int(input("새 판매 가격: "))

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            UPDATE Inventory
            SET stock_quantity = ?,
                selling_price = ?,
                last_updated = ?
            WHERE store_id = ? AND product_id = ?;
            """,
            (stock_quantity, selling_price, now, store_id, product_id)
        )

        if cur.rowcount == 0:
            print("수정된 데이터가 없습니다. 매장 ID와 상품 ID를 확인하세요.")
        else:
            conn.commit()
            print("재고 및 판매 가격 수정 완료!")

        conn.close()

    except ValueError:
        print("숫자를 입력해야 하는 항목이 있습니다.")
    except sqlite3.IntegrityError as error:
        print(f"재고 수정 중 데이터 무결성 오류가 발생했습니다: {error}")


def create_purchase_order():
    try:
        store_id = int(input("발주 매장 ID: "))
        supplier_id = int(input("공급업체 ID: "))
        product_id = int(input("발주 상품 ID: "))
        order_quantity = int(input("발주 수량: "))

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT 1
            FROM SupplierProduct
            WHERE supplier_id = ? AND product_id = ?;
            """,
            (supplier_id, product_id)
        )

        if cur.fetchone() is None:
            print("해당 공급업체가 공급하는 상품이 아닙니다. SupplierProduct 정보를 확인하세요.")
            conn.close()
            return

        cur.execute(
            """
            INSERT INTO PurchaseOrder (order_datetime, status, store_id, supplier_id)
            VALUES (?, 'ORDERED', ?, ?);
            """,
            (now, store_id, supplier_id)
        )

        po_id = cur.lastrowid

        cur.execute(
            """
            INSERT INTO PurchaseOrderItem (po_id, product_id, order_quantity)
            VALUES (?, ?, ?);
            """,
            (po_id, product_id, order_quantity)
        )

        conn.commit()
        conn.close()

        print(f"발주 요청 생성 완료! 발주번호: {po_id}")


    except ValueError:
        print("숫자를 입력해야 하는 항목이 있습니다.")
    except sqlite3.IntegrityError as error:
        print(f"발주 생성 중 데이터 무결성 오류가 발생했습니다: {error}")


def auto_reorder():
    try:
        store_id = int(input("자동 재주문을 실행할 매장 ID: "))
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                i.product_id,
                p.product_name,
                i.stock_quantity,
                i.reorder_level,
                i.reorder_quantity,
                sp.supplier_id,
                sup.supplier_name
            FROM Inventory i
            JOIN Product p ON i.product_id = p.product_id
            JOIN SupplierProduct sp ON i.product_id = sp.product_id
            JOIN Supplier sup ON sp.supplier_id = sup.supplier_id
            WHERE i.store_id = ?
              AND i.stock_quantity <= i.reorder_level
              AND sp.supply_price = (
                  SELECT MIN(sp2.supply_price)
                  FROM SupplierProduct sp2
                  WHERE sp2.product_id = i.product_id
              )
            ORDER BY sp.supplier_id, i.product_id;
            """,
            (store_id,)
        )

        low_stock_items = cur.fetchall()

        if not low_stock_items:
            print("자동 재주문이 필요한 상품이 없습니다.")
            conn.close()
            return

        orders_by_supplier = {}

        for item in low_stock_items:
            (
                product_id,
                product_name,
                stock_quantity,
                reorder_level,
                reorder_quantity,
                supplier_id,
                supplier_name
            ) = item

            if supplier_id not in orders_by_supplier:
                orders_by_supplier[supplier_id] = {
                    "supplier_name": supplier_name,
                    "items": []
                }

            orders_by_supplier[supplier_id]["items"].append(
                (product_id, product_name, stock_quantity, reorder_level, reorder_quantity)
            )

        created_orders = []

        for supplier_id, order_info in orders_by_supplier.items():
            cur.execute(
                """
                INSERT INTO PurchaseOrder (order_datetime, status, store_id, supplier_id)
                VALUES (?, 'ORDERED', ?, ?);
                """,
                (now, store_id, supplier_id)
            )

            po_id = cur.lastrowid

            for product_id, product_name, stock_quantity, reorder_level, reorder_quantity in order_info["items"]:
                cur.execute(
                    """
                    INSERT INTO PurchaseOrderItem (po_id, product_id, order_quantity)
                    VALUES (?, ?, ?);
                    """,
                    (po_id, product_id, reorder_quantity)
                )

            created_orders.append((po_id, order_info["supplier_name"], len(order_info["items"])))

        conn.commit()
        conn.close()

        print("자동 재주문 발주 생성 완료!")
        print_rows(
            created_orders,
            ["발주ID", "공급업체", "발주 상품 종류 수"]
        )

    except ValueError:
        print("매장 ID는 숫자로 입력해야 합니다.")
    except sqlite3.IntegrityError as error:
        print(f"자동 재주문 발주 생성 중 데이터 무결성 오류가 발생했습니다: {error}")


def supplier_menu():
    while True:
        print("\n=== 공급업체 메뉴 ===")
        print("1. 발주 요청 목록 조회")
        print("2. 납품 처리")
        print("3. 발주 상태 업데이트")
        print("4. 공급업체별 취급 브랜드 조회")
        print("0. 뒤로 가기")

        choice = input("메뉴를 선택하세요: ")

        if choice == "1":
            supplier_orders()
        elif choice == "2":
            process_delivery()
        elif choice == "3":
            update_order_status()
        elif choice == "4":
            supplier_brands()
        elif choice == "0":
            break
        else:
            print("잘못된 입력입니다.")


def supplier_orders():
    try:
        supplier_id = int(input("공급업체 ID: "))

        conn = get_connection()
        cur = conn.cursor()

        query = """
        SELECT
            po.po_id,
            po.order_datetime,
            po.status,
            s.store_name,
            p.product_name,
            poi.order_quantity,
            COALESCE(SUM(sri.received_quantity), 0) AS received_quantity
        FROM PurchaseOrder po
        JOIN Store s ON po.store_id = s.store_id
        JOIN PurchaseOrderItem poi ON po.po_id = poi.po_id
        JOIN Product p ON poi.product_id = p.product_id
        LEFT JOIN StockReceipt sr ON po.po_id = sr.po_id
        LEFT JOIN StockReceiptItem sri
            ON sr.receipt_id = sri.receipt_id
           AND poi.product_id = sri.product_id
        WHERE po.supplier_id = ?
        GROUP BY po.po_id, p.product_id
        ORDER BY po.order_datetime DESC;
        """

        cur.execute(query, (supplier_id,))
        rows = cur.fetchall()
        conn.close()

        print_rows(
            rows,
            ["발주ID", "발주일시", "상태", "매장", "상품명", "발주수량", "입고수량"]
        )

    except ValueError:
        print("공급업체 ID는 숫자로 입력해야 합니다.")


# 공급업체별 취급 브랜드 조회 함수
def supplier_brands():
    try:
        supplier_input = input("공급업체 ID 입력, 전체 조회는 Enter: ").strip()
        supplier_id = int(supplier_input) if supplier_input else None

        conn = get_connection()
        cur = conn.cursor()

        query = """
        SELECT
            sup.supplier_id,
            sup.supplier_name,
            b.brand_id,
            b.brand_name
        FROM SupplierBrand sb
        JOIN Supplier sup ON sb.supplier_id = sup.supplier_id
        JOIN Brand b ON sb.brand_id = b.brand_id
        WHERE (? IS NULL OR sup.supplier_id = ?)
        ORDER BY sup.supplier_name, b.brand_name;
        """

        cur.execute(query, (supplier_id, supplier_id))
        rows = cur.fetchall()
        conn.close()

        print_rows(
            rows,
            ["공급업체ID", "공급업체명", "브랜드ID", "브랜드명"]
        )

    except ValueError:
        print("공급업체 ID는 숫자로 입력해야 합니다.")


def process_delivery():
    try:
        po_id = int(input("납품 처리할 발주 ID: "))
        product_id = int(input("납품 상품 ID: "))
        received_quantity = int(input("실제 납품 수량: "))

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT po.store_id, poi.order_quantity
            FROM PurchaseOrder po
            JOIN PurchaseOrderItem poi ON po.po_id = poi.po_id
            WHERE po.po_id = ? AND poi.product_id = ?;
            """,
            (po_id, product_id)
        )

        result = cur.fetchone()

        if result is None:
            print("해당 발주 상품을 찾을 수 없습니다.")
            conn.close()
            return

        store_id, order_quantity = result

        cur.execute(
            """
            SELECT 1
            FROM Inventory
            WHERE store_id = ? AND product_id = ?;
            """,
            (store_id, product_id)
        )

        if cur.fetchone() is None:
            print("해당 매장에 해당 상품 재고 정보가 없어 입고 처리할 수 없습니다.")
            conn.close()
            return

        cur.execute(
            """
            SELECT COALESCE(SUM(sri.received_quantity), 0)
            FROM StockReceipt sr
            JOIN StockReceiptItem sri ON sr.receipt_id = sri.receipt_id
            WHERE sr.po_id = ? AND sri.product_id = ?;
            """,
            (po_id, product_id)
        )
        already_received = cur.fetchone()[0]

        if already_received + received_quantity > order_quantity:
            print("입고 수량이 발주 수량을 초과합니다.")
            conn.close()
            return

        cur.execute(
            """
            INSERT INTO StockReceipt (po_id, received_datetime)
            VALUES (?, ?);
            """,
            (po_id, now)
        )

        receipt_id = cur.lastrowid

        cur.execute(
            """
            INSERT INTO StockReceiptItem (receipt_id, product_id, received_quantity)
            VALUES (?, ?, ?);
            """,
            (receipt_id, product_id, received_quantity)
        )

        cur.execute(
            """
            UPDATE Inventory
            SET stock_quantity = stock_quantity + ?,
                last_updated = ?
            WHERE store_id = ? AND product_id = ?;
            """,
            (received_quantity, now, store_id, product_id)
        )

        new_received_total = already_received + received_quantity
        new_status = "FULFILLED" if new_received_total == order_quantity else "PARTIAL"

        cur.execute(
            """
            UPDATE PurchaseOrder
            SET status = ?
            WHERE po_id = ?;
            """,
            (new_status, po_id)
        )

        conn.commit()
        conn.close()

        print(f"납품 처리 완료! 입고번호: {receipt_id}, 발주 상태: {new_status}")

    except ValueError:
        print("숫자를 입력해야 하는 항목이 있습니다.")
    except sqlite3.IntegrityError as error:
        print(f"납품 처리 중 데이터 무결성 오류가 발생했습니다: {error}")


def update_order_status():
    try:
        po_id = int(input("상태를 수정할 발주 ID: "))
        status = input("새 상태 입력(ORDERED/PARTIAL/FULFILLED/CANCELLED): ").strip().upper()

        if status not in VALID_ORDER_STATUSES:
            print("올바르지 않은 상태입니다.")
            return

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            UPDATE PurchaseOrder
            SET status = ?
            WHERE po_id = ?;
            """,
            (status, po_id)
        )

        if cur.rowcount == 0:
            print("수정된 발주가 없습니다.")
        else:
            conn.commit()
            print("발주 상태 수정 완료!")

        conn.close()

    except ValueError:
        print("발주 ID는 숫자로 입력해야 합니다.")


def analysis_menu():
    while True:
        print("\n=== 분석 메뉴 ===")
        print("1. 매장별 인기 상품")
        print("2. 시·도별 인기 상품")
        print("3. 매출 상위 5개 매장")
        print("4. 코카콜라보다 펩시가 더 많이 판매된 매장 수")
        print("5. 우유와 함께 구매된 상품 TOP 3")
        print("6. 상품별 하위 타입 정보 조회")
        print("7. 공급업체별 취급 브랜드 조회")
        print("0. 뒤로 가기")

        choice = input("메뉴를 선택하세요: ")

        if choice == "1":
            top_products_by_store()
        elif choice == "2":
            top_products_by_region()
        elif choice == "3":
            top_stores_by_sales()
        elif choice == "4":
            pepsi_more_than_coke()
        elif choice == "5":
            products_bought_with_milk()
        elif choice == "6":
            product_subclass_report()
        elif choice == "7":
            supplier_brand_report()
        elif choice == "0":
            break
        else:
            print("잘못된 입력입니다.")


def top_products_by_store():
    conn = get_connection()
    cur = conn.cursor()

    query = """
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
    """

    cur.execute(query)
    rows = cur.fetchall()
    conn.close()

    print_rows(rows, ["매장명", "순위", "상품명", "총 판매수량"])


def top_products_by_region():
    conn = get_connection()
    cur = conn.cursor()

    query = """
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
    """

    cur.execute(query)
    rows = cur.fetchall()
    conn.close()

    print_rows(rows, ["시·도", "순위", "상품명", "총 판매수량"])


def top_stores_by_sales():
    conn = get_connection()
    cur = conn.cursor()

    query = """
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
    """

    cur.execute(query)
    rows = cur.fetchall()
    conn.close()

    print_rows(rows, ["매장명", "시·도", "시·군·구", "총매출", "판매건수"])


def pepsi_more_than_coke():
    conn = get_connection()
    cur = conn.cursor()

    query = """
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
    """

    cur.execute(query)
    rows = cur.fetchall()
    conn.close()

    print_rows(rows, ["펩시가 코카콜라보다 많이 판매된 매장 수"])


def products_bought_with_milk():
    conn = get_connection()
    cur = conn.cursor()

    query = """
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
    """

    cur.execute(query)
    rows = cur.fetchall()
    conn.close()

    print_rows(rows, ["함께 구매된 상품", "함께 구매된 수량"])


def product_subclass_report():
    conn = get_connection()
    cur = conn.cursor()

    query = """
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
        hp.health_product_type
    FROM Product p
    JOIN Brand b ON p.brand_id = b.brand_id
    LEFT JOIN FoodBeverageProduct fb ON p.product_id = fb.product_id
    LEFT JOIN DailyGoodsProduct dg ON p.product_id = dg.product_id
    LEFT JOIN HealthProduct hp ON p.product_id = hp.product_id
    ORDER BY p.product_id;
    """

    cur.execute(query)
    rows = cur.fetchall()
    conn.close()

    print_rows(
        rows,
        ["상품ID", "상품명", "브랜드", "하위타입", "유통기한", "재질", "건강용품유형"]
    )


# 분석용 공급업체별 취급 브랜드 조회 함수
def supplier_brand_report():
    conn = get_connection()
    cur = conn.cursor()

    query = """
    SELECT
        sup.supplier_name,
        b.brand_name
    FROM SupplierBrand sb
    JOIN Supplier sup ON sb.supplier_id = sup.supplier_id
    JOIN Brand b ON sb.brand_id = b.brand_id
    ORDER BY sup.supplier_name, b.brand_name;
    """

    cur.execute(query)
    rows = cur.fetchall()
    conn.close()

    print_rows(
        rows,
        ["공급업체명", "취급 브랜드"]
    )


def main():
    while True:
        print("\n==============================")
        print(" 이마트24 데이터베이스 시스템")
        print("==============================")
        print("1. 소비자 인터페이스")
        print("2. 매장 관리자 인터페이스")
        print("3. 공급업체 인터페이스")
        print("4. 분석 인터페이스")
        print("0. 종료")

        choice = input("메뉴를 선택하세요: ")

        if choice == "1":
            customer_menu()
        elif choice == "2":
            manager_menu()
        elif choice == "3":
            supplier_menu()
        elif choice == "4":
            analysis_menu()
        elif choice == "0":
            print("프로그램을 종료합니다.")
            break
        else:
            print("잘못된 입력입니다.")


if __name__ == "__main__":
    main()
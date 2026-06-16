import sqlite3
from datetime import datetime

DB_NAME = "emart24.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def print_rows(rows, headers):
    if not rows:
        print("조회 결과가 없습니다.")
        return

    print("-" * 80)
    print(" | ".join(headers))
    print("-" * 80)

    for row in rows:
        print(" | ".join(str(value) if value is not None else "NULL" for value in row))

    print("-" * 80)


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
        p.status,
        GROUP_CONCAT(pt.type_name, ', ') AS categories
    FROM Product p
    JOIN Brand b ON p.brand_id = b.brand_id
    LEFT JOIN ProductCategory pc ON p.product_id = pc.product_id
    LEFT JOIN ProductType pt ON pc.type_id = pt.type_id
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
        ["상품ID", "상품명", "바코드", "브랜드", "규격", "포장", "상태", "분류"]
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
        payment_method = input("결제 수단(cash/card/mobile): ").strip()

        if payment_method not in ("cash", "card", "mobile"):
            print("결제 수단은 cash, card, mobile 중 하나여야 합니다.")
            return

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
            INSERT INTO Sale (sale_datetime, total_amount, payment_method, store_id, customer_id)
            VALUES (?, ?, ?, ?, ?);
            """,
            (sale_datetime, total_amount, payment_method, store_id, customer_id)
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
            sa.total_amount,
            sa.payment_method
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
            ["판매ID", "구매일시", "매장", "상품명", "수량", "단가", "총액", "결제수단"]
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


def create_purchase_order():
    try:
        store_id = int(input("발주 매장 ID: "))
        supplier_id = int(input("공급업체 ID: "))
        product_id = int(input("발주 상품 ID: "))
        order_quantity = int(input("발주 수량: "))
        created_by = input("발주 생성자 이름 또는 ID: ")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO PurchaseOrder
                (order_datetime, status, created_by, fulfillment, store_id, supplier_id)
            VALUES (?, 'pending', ?, 'N', ?, ?);
            """,
            (now, created_by, store_id, supplier_id)
        )

        po_id = cur.lastrowid

        cur.execute(
            """
            INSERT INTO PurchaseOrderItem
                (po_id, product_id, order_quantity, received_quantity, received_datetime)
            VALUES (?, ?, ?, 0, NULL);
            """,
            (po_id, product_id, order_quantity)
        )

        conn.commit()
        conn.close()

        print(f"발주 요청 생성 완료! 발주번호: {po_id}")

    except ValueError:
        print("숫자를 입력해야 하는 항목이 있습니다.")


def supplier_menu():
    while True:
        print("\n=== 공급업체 메뉴 ===")
        print("1. 발주 요청 목록 조회")
        print("2. 납품 처리")
        print("3. 발주 상태 업데이트")
        print("0. 뒤로 가기")

        choice = input("메뉴를 선택하세요: ")

        if choice == "1":
            supplier_orders()
        elif choice == "2":
            process_delivery()
        elif choice == "3":
            update_order_status()
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
            po.fulfillment,
            s.store_name,
            p.product_name,
            poi.order_quantity,
            poi.received_quantity
        FROM PurchaseOrder po
        JOIN Store s ON po.store_id = s.store_id
        JOIN PurchaseOrderItem poi ON po.po_id = poi.po_id
        JOIN Product p ON poi.product_id = p.product_id
        WHERE po.supplier_id = ?
        ORDER BY po.order_datetime DESC;
        """

        cur.execute(query, (supplier_id,))
        rows = cur.fetchall()
        conn.close()

        print_rows(
            rows,
            ["발주ID", "발주일시", "상태", "납품완료", "매장", "상품명", "발주수량", "입고수량"]
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
            SELECT po.store_id
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

        store_id = result[0]

        cur.execute(
            """
            UPDATE PurchaseOrderItem
            SET received_quantity = ?,
                received_datetime = ?
            WHERE po_id = ? AND product_id = ?;
            """,
            (received_quantity, now, po_id, product_id)
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

        cur.execute(
            """
            UPDATE PurchaseOrder
            SET status = 'fulfilled',
                fulfillment = 'Y'
            WHERE po_id = ?;
            """,
            (po_id,)
        )

        conn.commit()
        conn.close()

        print("납품 처리 완료! 재고가 증가했습니다.")

    except ValueError:
        print("숫자를 입력해야 하는 항목이 있습니다.")


def update_order_status():
    try:
        po_id = int(input("상태를 수정할 발주 ID: "))
        status = input("새 상태 입력(pending/processing/fulfilled/cancelled): ")

        if status not in ("pending", "processing", "fulfilled", "cancelled"):
            print("올바르지 않은 상태입니다.")
            return

        fulfillment = "Y" if status == "fulfilled" else "N"

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            UPDATE PurchaseOrder
            SET status = ?,
                fulfillment = ?
            WHERE po_id = ?;
            """,
            (status, fulfillment, po_id)
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
        elif choice == "0":
            break
        else:
            print("잘못된 입력입니다.")


def top_products_by_store():
    conn = get_connection()
    cur = conn.cursor()

    query = """
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
    """

    cur.execute(query)
    rows = cur.fetchall()
    conn.close()

    print_rows(rows, ["매장명", "상품명", "총 판매수량"])


def top_products_by_region():
    conn = get_connection()
    cur = conn.cursor()

    query = """
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
    """

    cur.execute(query)
    rows = cur.fetchall()
    conn.close()

    print_rows(rows, ["시·도", "상품명", "총 판매수량"])


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
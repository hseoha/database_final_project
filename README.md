# 이마트24 데이터베이스 프로젝트

## 1. 프로젝트 개요

본 프로젝트는 이마트24를 대상으로 상품, 매장, 재고, 고객, 판매, 발주, 입고, 공급업체 정보를 관리하기 위한 SQLite 기반 데이터베이스 시스템이다.

Python과 SQLite를 사용하여 데이터베이스를 생성하고, 샘플 데이터를 삽입하며, CLI(Command Line Interface)를 통해 소비자, 매장 관리자, 공급업체, 데이터 분석 담당자용 기능을 실행할 수 있도록 구현하였다.

## 2. 파일 구성

```text
database_final_project/
├── schema.sql
├── create_db.py
├── insert_sample_data.py
├── main_cli.py
├── sample_queries.sql
├── README.md
└── docs/
```

## 3. 파일 설명

### schema.sql

SQLite 데이터베이스의 relation을 생성하는 SQL 파일이다.  
Retailer, Store, Customer, Brand, Product, FoodBeverageProduct, DailyGoodsProduct, HealthProduct, Category, ProductCategory, Supplier, SupplierProduct, Inventory, Sale, SaleItem, PurchaseOrder, PurchaseOrderItem, StockReceipt, StockReceiptItem 테이블을 정의한다.

각 테이블에는 Primary Key, Foreign Key, CHECK constraint, UNIQUE constraint가 포함되어 있으며, 자주 사용되는 검색 및 조인 조건에 대해 index를 생성한다.

### create_db.py

`schema.sql` 파일을 실행하여 SQLite 데이터베이스 파일인 `emart24.db`를 생성한다.  
기존 테이블이 있으면 삭제한 뒤 다시 생성하므로, 데이터베이스 구조를 처음부터 새로 만들 때 사용한다.

### insert_sample_data.py

프로젝트 테스트에 필요한 샘플 데이터를 데이터베이스에 삽입한다.  
매장, 고객, 브랜드, 상품, 상품 하위 타입, 카테고리, 공급업체, 재고, 판매 내역, 발주 내역, 입고 내역 등의 데이터를 포함한다.

### main_cli.py

사용자 인터페이스 역할을 하는 Python CLI 프로그램이다.  
다음 네 가지 인터페이스를 제공한다.

1. 소비자 인터페이스
2. 매장 관리자 인터페이스
3. 공급업체 인터페이스
4. 분석 인터페이스

### sample_queries.sql

프로젝트 명세서에서 요구한 분석용 sample query를 정리한 SQL 파일이다.  
매장별 상위 20개 인기 상품, 시·도별 상위 20개 인기 상품, 매출 상위 5개 매장, 브랜드별 판매량 비교, 함께 구매된 상품 분석, 재고 부족 상품 조회, 발주 및 입고 현황 조회, 상품 하위 타입 조회, 자동 재주문 대상 상품 조회 쿼리를 포함한다.

### docs/

ER diagram, ER 설명문서, relational schema 문서, 사용자 인터페이스 기능 설명문서 등 최종 제출용 문서를 저장하는 폴더이다.

## 4. 실행 방법

### 1단계. 데이터베이스 생성

터미널에서 프로젝트 폴더로 이동한 뒤 다음 명령어를 실행한다.

```bash
python3 create_db.py
```

실행 후 `emart24.db` 파일이 생성된다.

### 2단계. 샘플 데이터 삽입

```bash
python3 insert_sample_data.py
```

샘플 데이터가 데이터베이스에 삽입된다.

### 3단계. CLI 프로그램 실행

```bash
python3 main_cli.py
```

실행하면 다음과 같은 메뉴가 표시된다.

```text
==============================
 이마트24 데이터베이스 시스템
==============================
1. 소비자 인터페이스
2. 매장 관리자 인터페이스
3. 공급업체 인터페이스
4. 분석 인터페이스
0. 종료
```

## 5. 주요 기능

### 소비자 인터페이스

- 상품명 또는 브랜드명 기준 상품 검색
- 상품 상세 정보, 상품 하위 타입 정보 및 매장별 재고 조회
- 상품 구매 및 판매 내역 생성
- 회원 고객의 구매 내역 조회

### 매장 관리자 인터페이스

- 매장별 재고 조회
- 재고 부족 상품 조회
- 재고 수량 및 판매 가격 수정
- 발주 요청 생성
- 자동 재주문 발주 생성

자동 재주문 발주 생성 기능은 특정 매장의 재고 수량이 재주문 기준 수량 이하인 상품을 조회한 뒤, 공급업체별로 `PurchaseOrder`와 `PurchaseOrderItem`을 자동 생성한다.

### 공급업체 인터페이스

- 공급업체별 발주 요청 목록 조회
- 납품 처리
- 발주 상태 업데이트

납품 처리는 `StockReceipt`와 `StockReceiptItem` 테이블에 기록되며, 입고 처리 후 해당 매장의 `Inventory` 수량이 증가한다.

### 분석 인터페이스

- 매장별 상위 20개 인기 상품 조회
- 시·도별 상위 20개 인기 상품 조회
- 매출 상위 5개 매장 조회
- 코카콜라보다 펩시가 더 많이 판매된 매장 수 조회
- 우유와 함께 구매된 상품 TOP 3 조회
- 상품별 하위 타입 정보 조회

## 6. 주요 테이블 설명

### Retailer / Store

`Retailer`는 유통업체 정보를 저장하고, `Store`는 유통업체가 소유한 각 매장의 이름, 주소, 도시, 시·도, 영업 시간을 저장한다.

### Customer

`Customer`는 회원 고객 정보를 저장한다. 고객의 전화번호, 이메일, 생년월일은 선택적으로 저장될 수 있으며, 개인정보 제공 동의 여부는 `consent_phone`, `consent_email`, `consent_birthdate` 속성으로 관리한다.

### Brand / Product / Product Subclass / Category / ProductCategory

`Brand`는 상품 브랜드 정보를 저장하고, `Product`는 개별 상품의 이름, 바코드, 규격, 포장 형태, 브랜드 정보를 저장한다.

`FoodBeverageProduct`, `DailyGoodsProduct`, `HealthProduct`는 `Product`의 하위 타입을 표현하는 테이블이다. `FoodBeverageProduct`는 식품 및 음료 상품의 유통기한을 저장하고, `DailyGoodsProduct`는 생활용품의 재질을 저장하며, `HealthProduct`는 건강 관련 상품의 제형을 저장한다. 각 하위 타입 테이블의 `product_id`는 `Product(product_id)`를 참조하는 기본키이자 외래키이다.

### Supplier / SupplierProduct

`Supplier`는 공급업체 정보를 저장한다. `SupplierProduct`는 공급업체가 공급할 수 있는 상품과 공급 가격을 저장한다.

### Inventory

`Inventory`는 매장별 상품 재고 정보를 저장한다. 동일한 상품이라도 매장에 따라 재고 수량과 판매 가격이 다를 수 있으므로, 기본키는 `(store_id, product_id)`로 설정한다. 또한 `reorder_level`과 `reorder_quantity`를 통해 자동 재주문 발주 생성 기능에서 사용할 재주문 기준과 발주 수량을 관리한다.

### Sale / SaleItem

`Sale`은 판매 건 단위의 정보를 저장한다. 비회원 구매를 허용하기 위해 `customer_id`는 NULL이 가능하다.

`SaleItem`은 하나의 판매 건에 포함된 상품, 수량, 판매 당시 단가, 할인 금액을 저장한다.

### PurchaseOrder / PurchaseOrderItem

`PurchaseOrder`는 매장에서 공급업체에 요청한 발주 정보를 저장한다. 발주 상태는 `ORDERED`, `PARTIAL`, `FULFILLED`, `CANCELLED` 중 하나로 관리한다. 발주는 매장 관리자가 수동으로 생성할 수도 있고, 재고 부족 상품을 기준으로 자동 재주문 기능을 통해 생성할 수도 있다.

`PurchaseOrderItem`은 발주에 포함된 상품과 발주 수량을 저장한다.

### StockReceipt / StockReceiptItem

`StockReceipt`는 발주 상품이 실제로 입고된 시각을 저장한다.  
`StockReceiptItem`은 입고된 상품과 실제 입고 수량을 저장한다.

이를 통해 하나의 발주가 여러 번에 나누어 부분 입고되는 상황을 표현할 수 있다.

## 7. 실행 환경

- Python 3
- SQLite3
- VSCode

SQLite3는 Python 표준 라이브러리인 `sqlite3` 모듈을 사용하므로 별도 설치가 필요하지 않다.

## 8. 참고

데이터 파일 자체인 `emart24.db`는 최종 제출 ZIP에 포함하지 않고, 필요한 경우 별도 클라우드 링크를 통해 제공한다. `insert_sample_data.py`는 데이터베이스 구조와 기능을 확인하기 위한 샘플 데이터 삽입 코드이다.

JupyterLab 또는 Anaconda 환경은 SQL 쿼리 결과를 확인하기 위한 보조 실습 환경으로 사용할 수 있다.  
최종 실행은 Python 파일을 기준으로 하며, `create_db.py`, `insert_sample_data.py`, `main_cli.py`를 순서대로 실행하면 된다.

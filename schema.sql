PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS StockReceiptItem;
DROP TABLE IF EXISTS StockReceipt;
DROP TABLE IF EXISTS PurchaseOrderItem;
DROP TABLE IF EXISTS PurchaseOrder;
DROP TABLE IF EXISTS SupplierProduct;
DROP TABLE IF EXISTS SaleItem;
DROP TABLE IF EXISTS Sale;
DROP TABLE IF EXISTS Inventory;
DROP TABLE IF EXISTS ProductCategory;
DROP TABLE IF EXISTS Category;
DROP TABLE IF EXISTS FoodBeverageProduct;
DROP TABLE IF EXISTS DailyGoodsProduct;
DROP TABLE IF EXISTS HealthProduct;
DROP TABLE IF EXISTS Product;
DROP TABLE IF EXISTS Supplier;
DROP TABLE IF EXISTS Customer;
DROP TABLE IF EXISTS Store;
DROP TABLE IF EXISTS Brand;
DROP TABLE IF EXISTS Retailer;

CREATE TABLE Retailer (
    retailer_id INTEGER PRIMARY KEY,
    retailer_name TEXT NOT NULL
);

CREATE TABLE Store (
    store_id INTEGER PRIMARY KEY,
    store_name TEXT NOT NULL,
    store_address TEXT,
    city TEXT,
    province TEXT,
    opening_time TEXT,
    closing_time TEXT,
    retailer_id INTEGER NOT NULL,
    FOREIGN KEY (retailer_id) REFERENCES Retailer(retailer_id)
);

CREATE TABLE Customer (
    customer_id INTEGER PRIMARY KEY,
    customer_name TEXT NOT NULL,
    customer_phone TEXT,
    customer_email TEXT,
    customer_birth_date TEXT,
    consent_phone TEXT CHECK (consent_phone IN ('Y', 'N')),
    consent_email TEXT CHECK (consent_email IN ('Y', 'N')),
    consent_birthdate TEXT CHECK (consent_birthdate IN ('Y', 'N'))
);

CREATE TABLE Brand (
    brand_id INTEGER PRIMARY KEY,
    brand_name TEXT NOT NULL
);

CREATE TABLE Product (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    barcode TEXT UNIQUE,
    specification TEXT,
    package_type TEXT,
    brand_id INTEGER NOT NULL,
    FOREIGN KEY (brand_id) REFERENCES Brand(brand_id)
);

CREATE TABLE FoodBeverageProduct (
    product_id INTEGER PRIMARY KEY,
    expiration_date TEXT,
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);

CREATE TABLE DailyGoodsProduct (
    product_id INTEGER PRIMARY KEY,
    material TEXT,
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);

CREATE TABLE HealthProduct (
    product_id INTEGER PRIMARY KEY,
    dosage_form TEXT,
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);

CREATE TABLE Category (
    category_id INTEGER PRIMARY KEY,
    category_name TEXT NOT NULL,
    parent_category_id INTEGER,
    FOREIGN KEY (parent_category_id) REFERENCES Category(category_id)
);

CREATE TABLE ProductCategory (
    product_id INTEGER,
    category_id INTEGER,
    PRIMARY KEY (product_id, category_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id),
    FOREIGN KEY (category_id) REFERENCES Category(category_id)
);

CREATE TABLE Supplier (
    supplier_id INTEGER PRIMARY KEY,
    supplier_name TEXT NOT NULL
);

CREATE TABLE SupplierProduct (
    supplier_id INTEGER,
    product_id INTEGER,
    supply_price INTEGER CHECK (supply_price > 0),
    PRIMARY KEY (supplier_id, product_id),
    FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);

CREATE TABLE Inventory (
    store_id INTEGER,
    product_id INTEGER,
    stock_quantity INTEGER CHECK (stock_quantity >= 0),
    selling_price INTEGER CHECK (selling_price > 0),
    reorder_level INTEGER CHECK (reorder_level >= 0),
    reorder_quantity INTEGER CHECK (reorder_quantity > 0),
    last_updated TEXT,
    PRIMARY KEY (store_id, product_id),
    FOREIGN KEY (store_id) REFERENCES Store(store_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);

CREATE TABLE Sale (
    sale_id INTEGER PRIMARY KEY,
    sale_datetime TEXT NOT NULL,
    total_amount INTEGER CHECK (total_amount >= 0),
    store_id INTEGER NOT NULL,
    customer_id INTEGER,
    FOREIGN KEY (store_id) REFERENCES Store(store_id),
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
);

CREATE TABLE SaleItem (
    sale_id INTEGER,
    product_id INTEGER,
    quantity INTEGER CHECK (quantity > 0),
    unit_price INTEGER CHECK (unit_price > 0),
    discount_amount INTEGER DEFAULT 0 CHECK (discount_amount >= 0),
    PRIMARY KEY (sale_id, product_id),
    FOREIGN KEY (sale_id) REFERENCES Sale(sale_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);

CREATE TABLE PurchaseOrder (
    po_id INTEGER PRIMARY KEY,
    order_datetime TEXT NOT NULL,
    status TEXT CHECK (status IN ('ORDERED', 'PARTIAL', 'FULFILLED', 'CANCELLED')),
    store_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    FOREIGN KEY (store_id) REFERENCES Store(store_id),
    FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id)
);

CREATE TABLE PurchaseOrderItem (
    po_id INTEGER,
    product_id INTEGER,
    order_quantity INTEGER CHECK (order_quantity > 0),
    PRIMARY KEY (po_id, product_id),
    FOREIGN KEY (po_id) REFERENCES PurchaseOrder(po_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);

CREATE TABLE StockReceipt (
    receipt_id INTEGER PRIMARY KEY,
    po_id INTEGER NOT NULL,
    received_datetime TEXT NOT NULL,
    FOREIGN KEY (po_id) REFERENCES PurchaseOrder(po_id)
);

CREATE TABLE StockReceiptItem (
    receipt_id INTEGER,
    product_id INTEGER,
    received_quantity INTEGER CHECK (received_quantity > 0),
    PRIMARY KEY (receipt_id, product_id),
    FOREIGN KEY (receipt_id) REFERENCES StockReceipt(receipt_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);

-- Indexes for frequently joined foreign keys and search/filter conditions
CREATE INDEX idx_store_retailer ON Store(retailer_id);
CREATE INDEX idx_store_region ON Store(province, city);
CREATE INDEX idx_store_province ON Store(province);
CREATE INDEX idx_product_brand ON Product(brand_id);
CREATE INDEX idx_product_barcode ON Product(barcode);
CREATE INDEX idx_foodbeverage_expiration ON FoodBeverageProduct(expiration_date);
CREATE INDEX idx_category_parent ON Category(parent_category_id);
CREATE INDEX idx_productcategory_category ON ProductCategory(category_id);
CREATE INDEX idx_supplierproduct_product ON SupplierProduct(product_id);
CREATE INDEX idx_inventory_product ON Inventory(product_id);
CREATE INDEX idx_sale_store ON Sale(store_id);
CREATE INDEX idx_sale_store_amount ON Sale(store_id, total_amount);
CREATE INDEX idx_sale_customer ON Sale(customer_id);
CREATE INDEX idx_sale_datetime ON Sale(sale_datetime);
CREATE INDEX idx_saleitem_product ON SaleItem(product_id);
CREATE INDEX idx_po_store ON PurchaseOrder(store_id);
CREATE INDEX idx_po_supplier ON PurchaseOrder(supplier_id);
CREATE INDEX idx_po_status ON PurchaseOrder(status);
CREATE INDEX idx_poi_product ON PurchaseOrderItem(product_id);
CREATE INDEX idx_receipt_po ON StockReceipt(po_id);
CREATE INDEX idx_receipt_datetime ON StockReceipt(received_datetime);
CREATE INDEX idx_receiptitem_product ON StockReceiptItem(product_id);
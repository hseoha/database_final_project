PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS PurchaseOrderItem;
DROP TABLE IF EXISTS PurchaseOrder;
DROP TABLE IF EXISTS SupplierProduct;
DROP TABLE IF EXISTS SaleItem;
DROP TABLE IF EXISTS Sale;
DROP TABLE IF EXISTS Inventory;
DROP TABLE IF EXISTS ProductCategory;
DROP TABLE IF EXISTS ProductType;
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

CREATE TABLE Brand (
    brand_id INTEGER PRIMARY KEY,
    brand_name TEXT NOT NULL UNIQUE
);

CREATE TABLE Store (
    store_id INTEGER PRIMARY KEY,
    store_name TEXT NOT NULL,
    store_address TEXT NOT NULL,
    city TEXT,
    province TEXT,
    opening_time TEXT,
    closing_time TEXT,
    store_phone TEXT,
    retailer_id INTEGER NOT NULL,
    FOREIGN KEY (retailer_id) REFERENCES Retailer(retailer_id)
);

CREATE TABLE Customer (
    customer_id INTEGER PRIMARY KEY,
    customer_name TEXT NOT NULL,
    customer_phone TEXT,
    customer_email TEXT,
    customer_birth_date TEXT,
    customer_join_date TEXT,
    membership_grade TEXT DEFAULT 'BASIC',
    consent_phone TEXT CHECK (consent_phone IN ('Y', 'N')),
    consent_email TEXT CHECK (consent_email IN ('Y', 'N')),
    consent_birthdate TEXT CHECK (consent_birthdate IN ('Y', 'N'))
);

CREATE TABLE Supplier (
    supplier_id INTEGER PRIMARY KEY,
    supplier_name TEXT NOT NULL,
    contact_name TEXT,
    supplier_phone TEXT,
    supplier_email TEXT,
    supplier_address TEXT
);

CREATE TABLE Product (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    barcode TEXT NOT NULL UNIQUE,
    specification TEXT,
    package_type TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    brand_id INTEGER NOT NULL,
    FOREIGN KEY (brand_id) REFERENCES Brand(brand_id)
);

CREATE TABLE ProductType (
    type_id INTEGER PRIMARY KEY,
    type_name TEXT NOT NULL,
    parent_type_id INTEGER,
    FOREIGN KEY (parent_type_id) REFERENCES ProductType(type_id)
);

CREATE TABLE ProductCategory (
    product_id INTEGER,
    type_id INTEGER,
    PRIMARY KEY (product_id, type_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id),
    FOREIGN KEY (type_id) REFERENCES ProductType(type_id)
);

CREATE TABLE Inventory (
    store_id INTEGER,
    product_id INTEGER,
    stock_quantity INTEGER NOT NULL CHECK (stock_quantity >= 0),
    selling_price INTEGER NOT NULL CHECK (selling_price >= 0),
    reorder_level INTEGER NOT NULL CHECK (reorder_level >= 0),
    reorder_quantity INTEGER NOT NULL CHECK (reorder_quantity > 0),
    last_updated TEXT,
    PRIMARY KEY (store_id, product_id),
    FOREIGN KEY (store_id) REFERENCES Store(store_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);

CREATE TABLE Sale (
    sale_id INTEGER PRIMARY KEY,
    sale_datetime TEXT NOT NULL,
    total_amount INTEGER NOT NULL CHECK (total_amount >= 0),
    payment_method TEXT CHECK (payment_method IN ('cash', 'card', 'mobile')),
    store_id INTEGER NOT NULL,
    customer_id INTEGER,
    FOREIGN KEY (store_id) REFERENCES Store(store_id),
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
);

CREATE TABLE SaleItem (
    sale_id INTEGER,
    product_id INTEGER,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price INTEGER NOT NULL CHECK (unit_price >= 0),
    discount_amount INTEGER DEFAULT 0 CHECK (discount_amount >= 0),
    PRIMARY KEY (sale_id, product_id),
    FOREIGN KEY (sale_id) REFERENCES Sale(sale_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);

CREATE TABLE SupplierProduct (
    supplier_id INTEGER,
    product_id INTEGER,
    supply_price INTEGER NOT NULL CHECK (supply_price >= 0),
    lead_time_days INTEGER CHECK (lead_time_days >= 0),
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    PRIMARY KEY (supplier_id, product_id),
    FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);

CREATE TABLE PurchaseOrder (
    po_id INTEGER PRIMARY KEY,
    order_datetime TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'fulfilled', 'cancelled')),
    created_by TEXT,
    fulfillment TEXT DEFAULT 'N' CHECK (fulfillment IN ('Y', 'N')),
    store_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    FOREIGN KEY (store_id) REFERENCES Store(store_id),
    FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id)
);

CREATE TABLE PurchaseOrderItem (
    po_id INTEGER,
    product_id INTEGER,
    order_quantity INTEGER NOT NULL CHECK (order_quantity > 0),
    received_quantity INTEGER DEFAULT 0 CHECK (received_quantity >= 0),
    received_datetime TEXT,
    PRIMARY KEY (po_id, product_id),
    FOREIGN KEY (po_id) REFERENCES PurchaseOrder(po_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);

CREATE INDEX idx_store_retailer ON Store(retailer_id);
CREATE INDEX idx_store_region ON Store(province, city);
CREATE INDEX idx_product_brand ON Product(brand_id);
CREATE INDEX idx_inventory_product ON Inventory(product_id);
CREATE INDEX idx_sale_store ON Sale(store_id);
CREATE INDEX idx_sale_customer ON Sale(customer_id);
CREATE INDEX idx_sale_datetime ON Sale(sale_datetime);
CREATE INDEX idx_saleitem_product ON SaleItem(product_id);
CREATE INDEX idx_po_store ON PurchaseOrder(store_id);
CREATE INDEX idx_po_supplier ON PurchaseOrder(supplier_id);
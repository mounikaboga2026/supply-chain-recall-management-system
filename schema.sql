PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Supplier (
 supplier_id TEXT PRIMARY KEY, supplier_name TEXT NOT NULL, country TEXT NOT NULL,
 risk_rating TEXT NOT NULL CHECK(risk_rating IN ('LOW','MEDIUM','HIGH')),
 active_from TEXT NOT NULL, active_to TEXT
);
CREATE TABLE IF NOT EXISTS MaterialLot (
 material_lot_id TEXT PRIMARY KEY, supplier_id TEXT NOT NULL REFERENCES Supplier(supplier_id),
 material_code TEXT NOT NULL, received_date TEXT NOT NULL, expiry_date TEXT NOT NULL,
 received_qty REAL NOT NULL CHECK(received_qty > 0), unit TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('AVAILABLE','CONSUMED','QUARANTINED','EXPIRED')),
 issue_type TEXT
);
CREATE TABLE IF NOT EXISTS Product (
 product_id TEXT PRIMARY KEY, product_name TEXT NOT NULL, category TEXT NOT NULL,
 unit TEXT NOT NULL, active_from TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS BOM (
 bom_id TEXT PRIMARY KEY, product_id TEXT NOT NULL REFERENCES Product(product_id),
 material_code TEXT NOT NULL, qty_per_unit REAL NOT NULL CHECK(qty_per_unit > 0),
 effective_from TEXT NOT NULL, effective_to TEXT
);
CREATE TABLE IF NOT EXISTS ProductionOrder (
 production_order_id TEXT PRIMARY KEY, product_id TEXT NOT NULL REFERENCES Product(product_id),
 bom_id TEXT NOT NULL REFERENCES BOM(bom_id), planned_qty REAL NOT NULL,
 actual_qty REAL NOT NULL, start_date TEXT NOT NULL, completion_date TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('PLANNED','RELEASED','COMPLETED','CANCELLED'))
);
CREATE TABLE IF NOT EXISTS ProductionConsumption (
 consumption_id TEXT PRIMARY KEY, production_order_id TEXT NOT NULL REFERENCES ProductionOrder(production_order_id),
 material_lot_id TEXT NOT NULL REFERENCES MaterialLot(material_lot_id),
 consumed_qty REAL NOT NULL CHECK(consumed_qty > 0)
);
CREATE TABLE IF NOT EXISTS FinishedLot (
 finished_lot_id TEXT PRIMARY KEY, production_order_id TEXT NOT NULL REFERENCES ProductionOrder(production_order_id),
 product_id TEXT NOT NULL REFERENCES Product(product_id), produced_qty REAL NOT NULL CHECK(produced_qty > 0),
 manufacture_date TEXT NOT NULL, expiry_date TEXT NOT NULL, status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS Shipment (
 shipment_id TEXT PRIMARY KEY, ship_date TEXT NOT NULL, carrier TEXT NOT NULL,
 warehouse_code TEXT NOT NULL, status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS Customer (
 customer_id TEXT PRIMARY KEY, customer_name TEXT NOT NULL, customer_type TEXT NOT NULL,
 region TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS Delivery (
 delivery_id TEXT PRIMARY KEY, shipment_id TEXT NOT NULL REFERENCES Shipment(shipment_id),
 finished_lot_id TEXT NOT NULL REFERENCES FinishedLot(finished_lot_id),
 customer_id TEXT NOT NULL REFERENCES Customer(customer_id),
 delivered_qty REAL NOT NULL CHECK(delivered_qty > 0), delivery_date TEXT NOT NULL,
 delivery_status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS RecallCase (
 recall_id TEXT PRIMARY KEY, trigger_type TEXT NOT NULL CHECK(trigger_type IN ('RAW','FINISHED')),
 trigger_lot_id TEXT NOT NULL, reason TEXT NOT NULL, opened_at TEXT NOT NULL,
 status TEXT NOT NULL, ground_truth_case INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS RecallAction (
 action_id TEXT PRIMARY KEY, recall_id TEXT NOT NULL REFERENCES RecallCase(recall_id),
 action_type TEXT NOT NULL, target_type TEXT NOT NULL, target_id TEXT NOT NULL,
 affected_qty REAL NOT NULL DEFAULT 0, action_date TEXT NOT NULL, outcome TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS RecallEvent (
 event_id TEXT PRIMARY KEY, recall_id TEXT NOT NULL REFERENCES RecallCase(recall_id),
 event_type TEXT NOT NULL, entity_type TEXT NOT NULL, entity_id TEXT NOT NULL,
 event_date TEXT NOT NULL, details TEXT
);
CREATE INDEX IF NOT EXISTS ix_consumption_raw ON ProductionConsumption(material_lot_id);
CREATE INDEX IF NOT EXISTS ix_consumption_wo ON ProductionConsumption(production_order_id);
CREATE INDEX IF NOT EXISTS ix_delivery_lot ON Delivery(finished_lot_id);
CREATE INDEX IF NOT EXISTS ix_delivery_customer ON Delivery(customer_id);
CREATE INDEX IF NOT EXISTS ix_recall_trigger ON RecallCase(trigger_lot_id);

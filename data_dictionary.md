# Data dictionary

All timestamps/dates use ISO-8601 `YYYY-MM-DD`. Quantities are numeric and measured in the row's `unit` unless specified. IDs are immutable primary keys.

| Entity | Primary key | Main fields / validation |
|---|---|---|
| Supplier | supplier_id | supplier_name required; country required; risk_rating LOW/MEDIUM/HIGH; active_from required; active_to optional and >= active_from |
| MaterialLot | material_lot_id | supplier_id FK; material_code required; received_date; expiry_date >= received_date; received_qty > 0; unit; status AVAILABLE/CONSUMED/QUARANTINED/EXPIRED; issue_type optional |
| Product | product_id | product_name, category, unit and active_from required |
| BOM | bom_id | product_id FK; material_code; qty_per_unit > 0; effective_from; effective_to optional and >= effective_from |
| ProductionOrder | production_order_id | product_id FK; bom_id FK; planned_qty and actual_qty > 0; start_date <= completion_date; status PLANNED/RELEASED/COMPLETED/CANCELLED |
| ProductionConsumption | consumption_id | production_order_id FK; material_lot_id FK; consumed_qty > 0; N:M bridge between work orders and material lots |
| FinishedLot | finished_lot_id | production_order_id FK; product_id FK; produced_qty > 0; manufacture_date; expiry_date >= manufacture_date; lifecycle status |
| Shipment | shipment_id | ship_date; carrier; warehouse_code; status |
| Customer | customer_id | customer_name; customer_type; region |
| Delivery | delivery_id | shipment_id FK; finished_lot_id FK; customer_id FK; delivered_qty > 0; delivery_date; delivery_status |
| RecallCase | recall_id | trigger_type RAW/FINISHED; trigger_lot_id; reason; opened_at; status; ground_truth_case internal evaluation metadata |
| RecallAction | action_id | recall_id FK; action_type; target_type; target_id; affected_qty >= 0; action_date; outcome |
| RecallEvent | event_id | recall_id FK; event_type; entity_type; entity_id; event_date; details |

## Cardinality and lifecycle

- Supplier 1:N MaterialLot.
- Product 1:N BOM and Product 1:N ProductionOrder.
- BOM 1:N ProductionOrder; ProductionOrder N:M MaterialLot through ProductionConsumption.
- ProductionOrder 1:N FinishedLot.
- FinishedLot 1:N Delivery; Shipment 1:N Delivery; Customer 1:N Delivery.
- RecallCase 1:N RecallAction and RecallCase 1:N RecallEvent.
- A recall trigger can be a raw or finished lot; the trigger ID is polymorphic and therefore validated by application logic rather than a conventional FK.
- Effective dates are retained on Supplier, BOM and Product. State changes are appended as RecallEvent/RecallAction records; do not overwrite event history.

## Naming

`RAWLOT-<supplier-id>-2026-000001`, `WO-2026-000001`, `FINLOT-000001`, `SHP-2026-000001`, `REC-2026-000001`.

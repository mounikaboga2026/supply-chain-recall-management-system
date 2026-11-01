# Supply Chain Traceability & Product Recall Management

A runnable synthetic-data project for tracing supplier raw-material lots through production, finished lots, shipments and customers, then simulating recall scope and completion.

## Stack
Python 3.10+, SQLite, Pandas, Streamlit. All data is synthetic; no external or personal data is used.

## Quick start (Windows PowerShell)
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python generator.py --scale starter
streamlit run app.py
```

## Full-scale dataset
```powershell
python generator.py --scale full --seed 20261022
```
Full-scale targets: 500 suppliers, 10,000 raw lots, 5,000 production orders, 8,000 finished lots and 20,000 deliveries. The starter scale uses the same generator and fixed seed.

## Reproducibility
Run the generator twice with the same `--scale` and `--seed`. CSVs are overwritten deterministically. `source_manifest.json` contains SHA-256 checksums and row counts. To compare two runs, copy the generated `data/` directory after the first run, regenerate, then compare manifest hashes.

## Outputs
- CSV per entity in `data/`
- `dataset.json` consolidated synthetic records
- `ground_truth.csv` separately stores planted anomalies and expected recall labels. Do not use it as model input.
- `anomaly_cases.csv` lists intentional exceptions.
- `source_manifest.json` captures seed, provenance, row counts and hashes.
- `validation_summary.csv` captures PK/FK, date and quantity checks.
- `supply_chain.db` SQLite database created by the generator.

## Workflow
1. Generate supplier/product/BOM/customer master records.
2. Generate material lots and work orders.
3. Link material consumption to valid work orders and produce finished lots.
4. Create shipments and deliveries referencing valid finished lots and customers.
5. Create recall triggers, trace downstream lots and record notification/quarantine actions.
6. Run validation and inspect the Streamlit dashboard.

## Important modeling note on exceptions
The four required edge cases are represented as labelled cases in `anomaly_cases.csv` and `ground_truth.csv`. They are intentionally not inserted as broken foreign keys into the clean operational tables. This preserves a valid baseline relational dataset while keeping negative scenarios explicit and testable. Extend `recall_engine.py` to run each anomaly as a scenario test before promoting it into an operational event stream.

## Validation
```powershell
python generator.py --scale starter
```
The command creates `validation_summary.csv`. Core checks cover primary-key uniqueness, foreign-key integrity, material/production date ordering, raw consumption bounds and finished-lot delivery reconciliation.

## Limitations / next steps
This is a working prototype, not a production recall platform. For production, add role-based access, authentication, audit-log immutability, transactional event sourcing, lot-level inventory by warehouse, partial returns, carrier scan events, effective-dated BOM version selection, multi-material consumption per work order, and automated notification integrations.

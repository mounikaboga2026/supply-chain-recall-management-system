"""Deterministic synthetic supply-chain generator and recall simulation."""
from __future__ import annotations
import argparse, json, random, sqlite3, hashlib
from pathlib import Path
from datetime import date, timedelta
import pandas as pd

SEED_DEFAULT = 20261022
TABLES = ["Supplier","MaterialLot","Product","BOM","ProductionOrder",
          "ProductionConsumption","FinishedLot","Shipment","Customer","Delivery",
          "RecallCase","RecallAction","RecallEvent"]

def dstr(d): return d.isoformat()

def make_dataset(out_dir="data", scale="starter", seed=SEED_DEFAULT):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    n = {"starter": (30, 300, 150, 240, 600),
         "full": (500, 10000, 5000, 8000, 20000)}[scale]
    ns, nr, nw, nf, nd = n
    start = date(2026,1,1)

    suppliers=[]
    for i in range(1,ns+1):
        suppliers.append(dict(supplier_id=f"SUP-{i:06d}", supplier_name=f"Supplier {i:04d}",
          country=rng.choice(["India","Vietnam","Germany","Japan","USA"]),
          risk_rating=rng.choices(["LOW","MEDIUM","HIGH"],[.65,.28,.07])[0],
          active_from="2024-01-01", active_to=None))
    products=[dict(product_id=f"PROD-{i:03d}",product_name=f"Product {i:02d}",
                   category=rng.choice(["Food","Personal Care","Industrial"]),unit="unit",active_from="2025-01-01")
              for i in range(1,11)]
    boms=[]
    for p in products:
        for m in range(1,4):
            boms.append(dict(bom_id=f"BOM-{p['product_id']}-{m}",product_id=p["product_id"],
                material_code=f"MAT-{m:03d}",qty_per_unit=round(rng.uniform(.1,1.5),3),
                effective_from="2025-01-01",effective_to=None))
    bom_by_product={p["product_id"]:[b for b in boms if b["product_id"]==p["product_id"]] for p in products}
    customers=[dict(customer_id=f"CUS-{i:06d}",customer_name=f"Customer {i:05d}",
                    customer_type=rng.choice(["RETAILER","DISTRIBUTOR","HOSPITALITY"]),
                    region=rng.choice(["North","South","East","West","Central"])) for i in range(1, max(51, nd//4)+1)]

    raw=[]
    for i in range(1,nr+1):
        sup=suppliers[(i-1)%ns]
        received=start+timedelta(days=rng.randrange(240))
        raw.append(dict(material_lot_id=f"RAWLOT-{sup['supplier_id']}-2026-{i:06d}",
          supplier_id=sup["supplier_id"],material_code=f"MAT-{rng.randint(1,3):03d}",
          received_date=dstr(received),expiry_date=dstr(received+timedelta(days=rng.randint(180,500))),
          received_qty=round(rng.uniform(500,5000),2),unit="kg",
          status="AVAILABLE",issue_type=None))
    # Select contamination deterministically, but do not expose label in input tables.
    contaminated_raw=set(rng.sample([x["material_lot_id"] for x in raw], max(2, min(8,nr//100))))
    # Keep a map of lot material codes to ensure valid BOM consumption.
    raw_by_material={}
    for r in raw: raw_by_material.setdefault(r["material_code"],[]).append(r)
    raw_remaining={r["material_lot_id"]:r["received_qty"] for r in raw}

    orders=[]; consumptions=[]; finished=[]; wo_to_finished={}
    for i in range(1,nw+1):
        p=rng.choice(products); bom=rng.choice(bom_by_product[p["product_id"]])
        qty=round(rng.uniform(100,700),2)
        day=start+timedelta(days=rng.randrange(250))
        wo=f"WO-2026-{i:06d}"
        orders.append(dict(production_order_id=wo,product_id=p["product_id"],bom_id=bom["bom_id"],
             planned_qty=qty,actual_qty=qty,start_date=dstr(day),completion_date=dstr(day+timedelta(days=rng.randint(0,3))),
             status="COMPLETED"))
        # consume a matching material lot; retry other lots if selected one depleted
        need=qty*bom["qty_per_unit"]
        candidates=raw_by_material.get(bom["material_code"],[])
        candidates=sorted(candidates,key=lambda x: raw_remaining[x["material_lot_id"]],reverse=True)
        chosen=None
        for r in candidates:
            if raw_remaining[r["material_lot_id"]] >= need:
                chosen=r; break
        if chosen is None:
            # Use smaller production quantity where supply is constrained.
            chosen=max(candidates,key=lambda x:raw_remaining[x["material_lot_id"]])
            actual=min(qty, raw_remaining[chosen["material_lot_id"]]/bom["qty_per_unit"])
            actual=max(1,actual); need=actual*bom["qty_per_unit"]
            orders[-1]["actual_qty"]=round(actual,2); orders[-1]["planned_qty"]=round(actual,2)
        raw_remaining[chosen["material_lot_id"]]-=need
        cid=f"CON-{i:06d}"
        consumptions.append(dict(consumption_id=cid,production_order_id=wo,
                                 material_lot_id=chosen["material_lot_id"],consumed_qty=round(need,2)))
        # Split selected work orders so the finished-lot target is exact at each scale.
        extra_lots = max(0, nf - nw)
        lot_count = 2 if i <= extra_lots else 1
        lotids=[]
        if lot_count == 1:
            quantities=[round(orders[-1]["actual_qty"],2)]
        else:
            first=round(orders[-1]["actual_qty"]*rng.uniform(.35,.65),2)
            quantities=[first,round(orders[-1]["actual_qty"]-first,2)]
        for q in quantities:
            fid=f"FINLOT-{len(finished)+1:06d}"
            finished.append(dict(finished_lot_id=fid,production_order_id=wo,product_id=p["product_id"],
                produced_qty=q,manufacture_date=orders[-1]["completion_date"],
                expiry_date=dstr(day+timedelta(days=365)),status="RELEASED"))
            lotids.append(fid)
        wo_to_finished[wo]=lotids

    # Update raw statuses from consumed quantities.
    consumed_by_raw={}
    for c in consumptions: consumed_by_raw[c["material_lot_id"]]=consumed_by_raw.get(c["material_lot_id"],0)+c["consumed_qty"]
    for r in raw:
        r["status"]="CONSUMED" if consumed_by_raw.get(r["material_lot_id"],0)>0 else "AVAILABLE"

    shipments=[]; deliveries=[]; delivered_by_lot={}
    shipment_count=max(1, min(nd, int(nd/3)))
    for i in range(1,shipment_count+1):
        day=start+timedelta(days=rng.randrange(280))
        shipments.append(dict(shipment_id=f"SHP-2026-{i:06d}",ship_date=dstr(day),
             carrier=rng.choice(["BlueDart","DHL","FedEx","LocalCarrier"]),
             warehouse_code=f"WH-{rng.randint(1,8):02d}",status="DISPATCHED"))
    # Create exactly the requested delivery count while never exceeding lot production.
    base_deliveries, extra_deliveries = divmod(nd, len(finished))
    for idx, lot in enumerate(finished):
        parts = base_deliveries + (1 if idx < extra_deliveries else 0)
        remaining=round(lot["produced_qty"],2)
        for part in range(parts):
            q=round(remaining/(parts-part),2) if part < parts-1 else remaining
            q=min(q,remaining)
            sh=rng.choice(shipments); cu=rng.choice(customers)
            deliveries.append(dict(delivery_id=f"DEL-{len(deliveries)+1:07d}",shipment_id=sh["shipment_id"],
                finished_lot_id=lot["finished_lot_id"],customer_id=cu["customer_id"],
                delivered_qty=q,delivery_date=sh["ship_date"],delivery_status="DELIVERED"))
            delivered_by_lot[lot["finished_lot_id"]]=delivered_by_lot.get(lot["finished_lot_id"],0)+q
            remaining=round(remaining-q,2)

    # Edge cases are explicit and recorded in ground truth. Deliberate invalid FKs are
    # represented in anomaly_cases.csv, not inserted into relational core tables.
    anomaly_rows=[]
    if finished:
        anomaly_rows.append(dict(anomaly_id="ANOM-001",issue_type="MISSING_INPUT_LOT",
            entity_type="FinishedLot",entity_id=finished[0]["finished_lot_id"],
            description="Synthetic exception: genealogy edge references a missing raw lot.",
            expected_detection="Flag broken genealogy; exclude from valid traversal."))
        anomaly_rows.append(dict(anomaly_id="ANOM-002",issue_type="DELIVERED_EXCEEDS_PRODUCED",
            entity_type="FinishedLot",entity_id=finished[1]["finished_lot_id"],
            description="Synthetic exception: attempted delivery is greater than produced quantity.",
            expected_detection="Flag quantity reconciliation failure."))
        anomaly_rows.append(dict(anomaly_id="ANOM-003",issue_type="MISSED_CUSTOMER_NOTIFICATION",
            entity_type="FinishedLot",entity_id=finished[2]["finished_lot_id"],
            description="Synthetic exception: one downstream customer is intentionally omitted from recall actions.",
            expected_detection="Flag notification coverage below 100%."))
        anomaly_rows.append(dict(anomaly_id="ANOM-004",issue_type="RECALLED_STOCK_AVAILABLE",
            entity_type="FinishedLot",entity_id=finished[3]["finished_lot_id"],
            description="Synthetic exception: recalled stock remains in saleable status.",
            expected_detection="Flag recall inventory not quarantined."))
    # Recall cases: include a raw contaminated trigger and one finished trigger.
    recall_cases=[]; actions=[]; events=[]; truth=[]
    raw_lookup={r["material_lot_id"]:r for r in raw}
    consumed_raw_ids={c["material_lot_id"] for c in consumptions}
    consumed_contaminated=sorted(contaminated_raw.intersection(consumed_raw_ids))
    trigger_raw=consumed_contaminated[0] if consumed_contaminated else sorted(consumed_raw_ids)[0]
    contaminated_raw.add(trigger_raw)
    recall_cases.append(dict(recall_id="REC-2026-000001",trigger_type="RAW",trigger_lot_id=trigger_raw,
       reason="Suspected supplier contamination",opened_at="2026-10-01",status="OPEN",ground_truth_case=1))
    truth.append(dict(record_type="RECALL_SCOPE",record_id="REC-2026-000001",label="CONTAMINATED_SOURCE",
       expected="All finished lots produced using trigger raw lot and all downstream deliveries."))
    # Find finished lots consuming the raw trigger.
    affected_wos={c["production_order_id"] for c in consumptions if c["material_lot_id"]==trigger_raw}
    affected_finished=[f for f in finished if f["production_order_id"] in affected_wos]
    for f in affected_finished:
        recall_id="REC-2026-000001"
        actions.append(dict(action_id=f"ACT-{len(actions)+1:07d}",recall_id=recall_id,action_type="QUARANTINE",
          target_type="FINISHED_LOT",target_id=f["finished_lot_id"],affected_qty=f["produced_qty"],
          action_date="2026-10-01",outcome="QUARANTINED"))
        events.append(dict(event_id=f"EVT-{len(events)+1:07d}",recall_id=recall_id,event_type="LOT_QUARANTINED",
          entity_type="FINISHED_LOT",entity_id=f["finished_lot_id"],event_date="2026-10-01",details="System-generated recall action"))
        for d in [x for x in deliveries if x["finished_lot_id"]==f["finished_lot_id"]]:
            actions.append(dict(action_id=f"ACT-{len(actions)+1:07d}",recall_id=recall_id,action_type="NOTIFY_CUSTOMER",
              target_type="CUSTOMER",target_id=d["customer_id"],affected_qty=d["delivered_qty"],
              action_date="2026-10-01",outcome="NOTIFIED"))
    # Finished-lot recall, for independent trigger scenario.
    ftrigger=finished[-1]
    recall_cases.append(dict(recall_id="REC-2026-000002",trigger_type="FINISHED",
       trigger_lot_id=ftrigger["finished_lot_id"],reason="Finished product quality deviation",
       opened_at="2026-10-03",status="OPEN",ground_truth_case=0))
    for d in [x for x in deliveries if x["finished_lot_id"]==ftrigger["finished_lot_id"]]:
        actions.append(dict(action_id=f"ACT-{len(actions)+1:07d}",recall_id="REC-2026-000002",
           action_type="NOTIFY_CUSTOMER",target_type="CUSTOMER",target_id=d["customer_id"],
           affected_qty=d["delivered_qty"],action_date="2026-10-03",outcome="NOTIFIED"))

    # Plant the missed notification anomaly by recording it as an expected exception.
    truth.extend([dict(record_type="ANOMALY",record_id=x["anomaly_id"],label=x["issue_type"],expected=x["expected_detection"])
                  for x in anomaly_rows])
    # Export CSVs and ground truth separately from input features.
    frames={
      "suppliers":suppliers,"material_lots":raw,"products":products,"bom":boms,
      "production_orders":orders,"production_consumption":consumptions,"finished_lots":finished,
      "shipments":shipments,"customers":customers,"deliveries":deliveries,
      "recall_cases":recall_cases,"recall_actions":actions,"recall_events":events,
      "anomaly_cases":anomaly_rows
    }
    columns_by_name = {
      "suppliers":["supplier_id","supplier_name","country","risk_rating","active_from","active_to"],
      "material_lots":["material_lot_id","supplier_id","material_code","received_date","expiry_date","received_qty","unit","status","issue_type"],
      "products":["product_id","product_name","category","unit","active_from"],
      "bom":["bom_id","product_id","material_code","qty_per_unit","effective_from","effective_to"],
      "production_orders":["production_order_id","product_id","bom_id","planned_qty","actual_qty","start_date","completion_date","status"],
      "production_consumption":["consumption_id","production_order_id","material_lot_id","consumed_qty"],
      "finished_lots":["finished_lot_id","production_order_id","product_id","produced_qty","manufacture_date","expiry_date","status"],
      "shipments":["shipment_id","ship_date","carrier","warehouse_code","status"],
      "customers":["customer_id","customer_name","customer_type","region"],
      "deliveries":["delivery_id","shipment_id","finished_lot_id","customer_id","delivered_qty","delivery_date","delivery_status"],
      "recall_cases":["recall_id","trigger_type","trigger_lot_id","reason","opened_at","status","ground_truth_case"],
      "recall_actions":["action_id","recall_id","action_type","target_type","target_id","affected_qty","action_date","outcome"],
      "recall_events":["event_id","recall_id","event_type","entity_type","entity_id","event_date","details"],
      "anomaly_cases":["anomaly_id","issue_type","entity_type","entity_id","description","expected_detection"]
    }
    for name,rows in frames.items():
        pd.DataFrame(rows, columns=columns_by_name[name]).to_csv(out/f"{name}.csv",index=False)
    pd.DataFrame(truth).to_csv(out/"ground_truth.csv",index=False)
    # JSON snapshot for interoperability.
    with open(out/"dataset.json","w",encoding="utf-8") as fp: json.dump(frames,fp,indent=2)
    manifest=[]
    for p in sorted(out.glob("*.csv"))+[out/"dataset.json"]:
        if p.exists():
            manifest.append({"file":p.name,"rows":sum(1 for _ in open(p,encoding="utf-8"))-1 if p.suffix==".csv" else None,
                             "sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
    (out/"source_manifest.json").write_text(json.dumps({"seed":seed,"scale":scale,"provenance":"Fully synthetic; no external personal or confidential data.","files":manifest},indent=2))
    return frames

def build_sqlite(data_dir="data", db_path="supply_chain.db"):
    data=Path(data_dir); db=Path(db_path)
    if db.exists(): db.unlink()
    con=sqlite3.connect(db); con.execute("PRAGMA foreign_keys=ON")
    con.executescript(Path(__file__).with_name("schema.sql").read_text())
    mapping={"suppliers":"Supplier","material_lots":"MaterialLot","products":"Product","bom":"BOM",
      "production_orders":"ProductionOrder","production_consumption":"ProductionConsumption",
      "finished_lots":"FinishedLot","shipments":"Shipment","customers":"Customer","deliveries":"Delivery",
      "recall_cases":"RecallCase","recall_actions":"RecallAction","recall_events":"RecallEvent"}
    for fname,table in mapping.items():
        csv=data/f"{fname}.csv"
        if not csv.exists(): continue
        df=pd.read_csv(csv)
        df=df.astype(object).where(pd.notnull(df),None)
        cols=list(df.columns)
        placeholders=",".join(["?"]*len(cols))
        sql=f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
        # Convert pandas NaN to None
        rows=[tuple(None if pd.isna(v) else v.item() if hasattr(v,"item") else v for v in row) for row in df.to_numpy()]
        con.executemany(sql,rows)
    con.commit(); con.close()

def validate(data_dir="data"):
    d=Path(data_dir); results=[]
    def check(name,passed,detail): results.append({"check":name,"passed":bool(passed),"detail":str(detail)})
    tables={p.stem:pd.read_csv(p) for p in d.glob("*.csv") if p.stem!="ground_truth"}
    for key,df in tables.items():
        pk={"suppliers":"supplier_id","material_lots":"material_lot_id","products":"product_id","bom":"bom_id",
            "production_orders":"production_order_id","production_consumption":"consumption_id","finished_lots":"finished_lot_id",
            "shipments":"shipment_id","customers":"customer_id","deliveries":"delivery_id","recall_cases":"recall_id",
            "recall_actions":"action_id","recall_events":"event_id"}.get(key)
        if pk: check(f"{key}: primary key unique",df[pk].is_unique,f"{df[pk].duplicated().sum()} duplicates")
    # FK checks in the valid core tables.
    checks=[("material_lots","supplier_id","suppliers","supplier_id"),
      ("bom","product_id","products","product_id"),
      ("production_orders","product_id","products","product_id"),
      ("production_orders","bom_id","bom","bom_id"),
      ("production_consumption","production_order_id","production_orders","production_order_id"),
      ("production_consumption","material_lot_id","material_lots","material_lot_id"),
      ("finished_lots","production_order_id","production_orders","production_order_id"),
      ("finished_lots","product_id","products","product_id"),
      ("deliveries","shipment_id","shipments","shipment_id"),
      ("deliveries","finished_lot_id","finished_lots","finished_lot_id"),
      ("deliveries","customer_id","customers","customer_id"),
      ("recall_actions","recall_id","recall_cases","recall_id"),
      ("recall_events","recall_id","recall_cases","recall_id")]
    for child,col,parent,pcol in checks:
        missing=~tables[child][col].isin(tables[parent][pcol])
        check(f"{child}.{col} -> {parent}.{pcol}",not missing.any(),f"{missing.sum()} orphan references")
    # Reconcile delivery totals to finished output.
    dsum=tables["deliveries"].groupby("finished_lot_id").delivered_qty.sum()
    produced=tables["finished_lots"].set_index("finished_lot_id").produced_qty
    over=(dsum>produced.reindex(dsum.index)+0.01).sum()
    check("delivered quantity does not exceed produced",over==0,f"{over} lots exceed production")
    # Consumption cannot exceed received lot quantity.
    csum=tables["production_consumption"].groupby("material_lot_id").consumed_qty.sum()
    received=tables["material_lots"].set_index("material_lot_id").received_qty
    overraw=(csum>received.reindex(csum.index)+0.01).sum()
    check("raw consumption does not exceed received",overraw==0,f"{overraw} raw lots over-consumed")
    # Date ordering
    mat=tables["material_lots"]
    check("material expiry after receipt",(pd.to_datetime(mat.expiry_date)>=pd.to_datetime(mat.received_date)).all(),"date order")
    po=tables["production_orders"]
    check("production completion after start",(pd.to_datetime(po.completion_date)>=pd.to_datetime(po.start_date)).all(),"date order")
    report=pd.DataFrame(results); report.to_csv(d/"validation_summary.csv",index=False)
    return report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--scale",choices=["starter","full"],default="starter")
    ap.add_argument("--seed",type=int,default=SEED_DEFAULT)
    ap.add_argument("--out",default="data")
    ap.add_argument("--db",default="supply_chain.db")
    args=ap.parse_args()
    make_dataset(args.out,args.scale,args.seed)
    build_sqlite(args.out,args.db)
    report=validate(args.out)
    print(report.to_string(index=False))
    print(f"\nCreated {args.scale} dataset in {args.out}; database: {args.db}")
if __name__=="__main__": main()

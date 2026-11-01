"""Genealogy traversal and recall scope evaluation."""
from pathlib import Path
import pandas as pd

def trace_raw_lot(raw_lot_id, data_dir="data"):
    d=Path(data_dir)
    cons=pd.read_csv(d/"production_consumption.csv")
    fin=pd.read_csv(d/"finished_lots.csv")
    deliveries=pd.read_csv(d/"deliveries.csv")
    orders=pd.read_csv(d/"production_orders.csv")
    customers=pd.read_csv(d/"customers.csv")
    hits=cons[cons.material_lot_id==raw_lot_id]
    wos=set(hits.production_order_id)
    affected=fin[fin.production_order_id.isin(wos)]
    downstream=deliveries[deliveries.finished_lot_id.isin(affected.finished_lot_id)]
    result=downstream.merge(customers,on="customer_id",how="left").merge(
        affected[["finished_lot_id","produced_qty","production_order_id"]],on="finished_lot_id",how="left")
    return {"production_orders":orders[orders.production_order_id.isin(wos)],
            "finished_lots":affected,"deliveries":result,
            "delivered_qty":float(downstream.delivered_qty.sum()),
            "customer_count":int(downstream.customer_id.nunique()),
            "finished_lot_count":int(affected.finished_lot_id.nunique())}

def recall_metrics(data_dir="data"):
    d=Path(data_dir)
    fin=pd.read_csv(d/"finished_lots.csv")
    delivery=pd.read_csv(d/"deliveries.csv")
    cases=pd.read_csv(d/"recall_cases.csv")
    actions=pd.read_csv(d/"recall_actions.csv")
    gt=pd.read_csv(d/"ground_truth.csv")
    total_delivered=delivery.delivered_qty.sum()
    notified=actions[actions.action_type=="NOTIFY_CUSTOMER"].target_id.nunique()
    return {
      "finished_lots":len(fin),"deliveries":len(delivery),"recall_cases":len(cases),
      "delivered_units":round(float(total_delivered),2),"notified_customers":int(notified),
      "quarantined_units":round(float(actions.loc[actions.action_type=="QUARANTINE","affected_qty"].sum()),2),
      "ground_truth_records":len(gt)
    }

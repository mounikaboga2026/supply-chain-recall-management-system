import streamlit as st
import pandas as pd
from pathlib import Path
from recall_engine import trace_raw_lot, recall_metrics
from generator import make_dataset, build_sqlite, validate

st.set_page_config(page_title="Supply Chain Recall Control Tower",layout="wide")
st.title("Supply Chain Traceability & Product Recall")
st.caption("Synthetic demonstration environment • fixed seed 20261022")
DATA=Path("data")

def load(name):
    p=DATA/f"{name}.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()

with st.sidebar:
    st.header("Dataset controls")
    scale=st.selectbox("Dataset scale",["starter","full"])
    if st.button("Generate dataset",type="primary"):
        with st.spinner("Generating synthetic data..."):
            make_dataset("data",scale,20261022)
            build_sqlite("data","supply_chain.db")
            validate("data")
        st.success(f"{scale.title()} dataset generated")
    st.caption("Full scale: 500 suppliers, 10,000 raw lots, 5,000 work orders, 8,000 finished lots, 20,000 deliveries.")

if not (DATA/"finished_lots.csv").exists():
    st.info("Generate the starter dataset from the sidebar, or run `python generator.py --scale starter`.")
    st.stop()

m=recall_metrics()
cols=st.columns(5)
for col,label,key in zip(cols,["Finished lots","Deliveries","Recall cases","Delivered units","Quarantined units"],
                         ["finished_lots","deliveries","recall_cases","delivered_units","quarantined_units"]):
    col.metric(label,m[key])

tabs=st.tabs(["Lot genealogy","Recall cases","Data explorer","Validation"])
with tabs[0]:
    st.subheader("Trace a raw material lot downstream")
    raw=load("material_lots")
    chosen=st.selectbox("Raw material lot",raw.material_lot_id.tolist())
    if st.button("Trace lot"):
        result=trace_raw_lot(chosen)
        a,b,c=st.columns(3)
        a.metric("Affected production orders",len(result["production_orders"]))
        b.metric("Affected finished lots",result["finished_lot_count"])
        c.metric("Downstream customers",result["customer_count"])
        st.write("Finished lots")
        st.dataframe(result["finished_lots"],use_container_width=True)
        st.write("Customer deliveries")
        st.dataframe(result["deliveries"],use_container_width=True)
with tabs[1]:
    st.subheader("Recall register")
    cases=load("recall_cases")
    st.dataframe(cases.drop(columns=["ground_truth_case"],errors="ignore"),use_container_width=True)
    actions=load("recall_actions")
    st.subheader("Recall actions")
    st.dataframe(actions,use_container_width=True)
    st.caption("Ground-truth labels are stored separately and are not shown as operational input.")
with tabs[2]:
    entity=st.selectbox("Choose entity",["suppliers","material_lots","products","bom","production_orders",
      "production_consumption","finished_lots","shipments","customers","deliveries","recall_cases","recall_actions"])
    df=load(entity)
    st.write(f"{len(df):,} rows")
    st.dataframe(df.head(500),use_container_width=True)
    st.download_button("Download selected CSV",df.to_csv(index=False),file_name=f"{entity}.csv",mime="text/csv")
with tabs[3]:
    report=load("validation_summary")
    if report.empty:
        st.warning("Run validation with `python generator.py --scale starter`.")
    else:
        st.metric("Checks passed",f"{int(report.passed.sum())}/{len(report)}")
        st.dataframe(report,use_container_width=True)

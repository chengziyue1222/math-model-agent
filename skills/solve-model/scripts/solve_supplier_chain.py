"""Solve a transparent decomposed supplier-chain baseline from raw 2021C inputs."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import milp, Bounds, LinearConstraint

CONV={"A":0.6,"B":0.66,"C":0.72}; DEMAND=28200.0
def write(root: Path, name: str, value) -> None:
    path=root/"results"/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def main(root: Path) -> None:
    raw=root/"data"/"raw"; book=next(raw.glob("*402*.xlsx")); transfer=next(raw.glob("*8*.xlsx")); sheets=pd.ExcelFile(book).sheet_names
    order=pd.read_excel(book,sheet_name=sheets[0]); supply=pd.read_excel(book,sheet_name=sheets[1]); loss=pd.read_excel(transfer)
    ids=order.iloc[:,0].astype(str).tolist(); materials=order.iloc[:,1].astype(str).tolist(); supply_values=supply.iloc[:,2:].to_numpy(float)
    robust=np.array([np.quantile(row[row>0],.25) if (row>0).any() else 0.0 for row in supply_values]); active=(supply_values>0).mean(axis=1); capacity=np.array([robust[i]/CONV[materials[i]] for i in range(len(ids))])
    score=(capacity/(capacity.max() or 1))*0.7+active*0.3; ranked=pd.DataFrame({"supplier_id":ids,"material":materials,"robust_raw_supply":robust,"product_equiv_capacity":capacity,"active_rate":active,"score":score}).sort_values("score",ascending=False).reset_index(drop=True); ranked["rank"]=np.arange(1,len(ranked)+1)
    avg_loss=float(loss.iloc[:,1:].to_numpy(float)[loss.iloc[:,1:].to_numpy(float)>0].mean()/100); required=DEMAND*1.015/(1-avg_loss); result=milp(np.ones(len(ids)),integrality=np.ones(len(ids)),bounds=Bounds(0,1),constraints=LinearConstraint(-capacity[None,:],-np.inf,-required))
    chosen=np.flatnonzero(result.x>.5) if result.success else np.array([],dtype=int); selected=ranked[ranked.supplier_id.isin([ids[i] for i in chosen])]
    ranked.to_csv(root/"results"/"supplier_ranking.csv",index=False); ranked.head(50).to_csv(root/"results"/"top50_suppliers.csv",index=False); selected.to_csv(root/"results"/"minimum_supplier_set.csv",index=False)
    material_array=np.asarray(materials); quantities=np.zeros(len(ids)); quantities[chosen]=np.minimum(robust[chosen],required*np.asarray([CONV[item] for item in material_array[chosen]])/max(len(chosen),1)); plan=pd.DataFrame({"supplier_id":ids,"material":materials,"week_01_raw_order":quantities}); plan.to_csv(root/"results"/"ordering_baseline.csv",index=False)
    spec={"model":"decomposition: consensus ranking + cardinality MILP","variables":"supplier activation and weekly raw orders","units":"raw m3 and product-equivalent m3","parameter_source":"official raw attachments","code_function":"solve_supplier_chain.main"}
    status="OPTIMAL" if result.success else "INFEASIBLE"; payload={"status":status,"solution":{"top50_supplier_ids":ranked.head(50).supplier_id.tolist(),"supplier_count":int(len(chosen)),"weekly_raw_orders":"results/ordering_baseline.csv"},"metrics":{"average_nonzero_loss":avg_loss,"required_product_equiv":required},"diagnostics":{"solver_message":result.message},"constraints":{"demand_product_equiv":DEMAND,"carrier_raw_capacity":48000},"baselines":{"equal_share":"not optimized"},"sensitivity":{},"uncertainty":{"rank_method":"lower-quartile supply capacity"},"warnings":["Q2 is disclosed as decomposed"],"metadata":{"seed":202107,"units":"m3"}}
    write(root,"model_specification.json",spec);write(root,"result_object.json",payload);write(root,"solver_validation.json",{"status":status,"selected_capacity":float(capacity[chosen].sum()*(1-avg_loss)) if len(chosen) else 0,"demand":DEMAND})

if __name__ == "__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--root",type=Path,required=True);main(parser.parse_args().root)

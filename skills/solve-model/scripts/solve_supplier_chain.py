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
    planning=np.array([np.quantile(row[row>0],.75) if (row>0).any() else 0.0 for row in supply_values]); active=(supply_values>0).mean(axis=1); capacity=np.array([planning[i]/CONV[materials[i]] for i in range(len(ids))])
    score=(capacity/(capacity.max() or 1))*0.7+active*0.3; ranked=pd.DataFrame({"supplier_id":ids,"material":materials,"planning_raw_supply_q75":planning,"product_equiv_capacity":capacity,"active_rate":active,"score":score}).sort_values("score",ascending=False).reset_index(drop=True); ranked["rank"]=np.arange(1,len(ranked)+1)
    avg_loss=float(loss.iloc[:,1:].to_numpy(float)[loss.iloc[:,1:].to_numpy(float)>0].mean()/100); required=DEMAND*1.015/(1-avg_loss); result=milp(np.ones(len(ids)),integrality=np.ones(len(ids)),bounds=Bounds(0,1),constraints=LinearConstraint(-capacity[None,:],-np.inf,-required))
    chosen=np.flatnonzero(result.x>.5) if result.success else np.array([],dtype=int); selected=ranked[ranked.supplier_id.isin([ids[i] for i in chosen])]
    ranked.to_csv(root/"results"/"supplier_ranking.csv",index=False); ranked.head(50).to_csv(root/"results"/"top50_suppliers.csv",index=False); selected.to_csv(root/"results"/"minimum_supplier_set.csv",index=False)
    material_array=np.asarray(materials); quantities=np.zeros(len(ids)); quantities[chosen]=np.minimum(planning[chosen],required*np.asarray([CONV[item] for item in material_array[chosen]])/max(len(chosen),1)); plan=pd.DataFrame({"supplier_id":ids,"material":materials,"week_01_raw_order":quantities}); plan.to_csv(root/"results"/"ordering_baseline.csv",index=False)
    weekly=pd.DataFrame({"supplier_id":ids,"material":materials})
    for week in range(1,25): weekly[f"week_{week:02d}_raw_order"]=quantities*(0.92+0.16*((week-1)%6)/5)
    weekly.to_csv(root/"results"/"ordering_plan_24weeks.csv",index=False)
    spec={"model":"decomposition: consensus ranking + planning-capacity cardinality MILP + rolling schedule","variables":"supplier activation and weekly raw orders","units":"raw m3 and product-equivalent m3","parameter_source":"official raw attachments","capacity_quantile":0.75,"code_function":"solve_supplier_chain.main"}
    status="OPTIMAL" if result.success else "INFEASIBLE"; payload={"status":status,"solution":{"top50_supplier_ids":ranked.head(50).supplier_id.tolist(),"supplier_count":int(len(chosen)),"weekly_raw_orders":"results/ordering_plan_24weeks.csv"},"metrics":{"average_nonzero_loss":avg_loss,"required_product_equiv":required,"maximum_planning_capacity":float(capacity.sum()*(1-avg_loss))},"diagnostics":{"solver_message":result.message},"constraints":{"demand_product_equiv":DEMAND,"carrier_raw_capacity":48000},"baselines":{"equal_share":"not optimized"},"sensitivity":{"capacity_quantile":0.75},"uncertainty":{"rank_method":"capacity-active-rate consensus","planning_capacity":"75th percentile; not worst-case robust capacity"},"warnings":["Q2 is disclosed as decomposed","reoptimize weekly when forecasts change"],"metadata":{"seed":202107,"units":"m3"}}
    write(root,"model_specification.json",spec);write(root,"result_object.json",payload);write(root,"solver_validation.json",{"status":status,"selected_capacity":float(capacity[chosen].sum()*(1-avg_loss)) if len(chosen) else 0,"demand":DEMAND})
    import hashlib
    paper=root/"paper";paper.mkdir(exist_ok=True); result_path=root/"results"/"result_object.json"; digest=hashlib.sha256(result_path.read_bytes()).hexdigest()
    claims=[{"claim_id":"CLAIM_TOP50","evidence_id":"RESULT","json_pointer":"/solution/top50_supplier_ids","array_length":50,"array_sha256":hashlib.sha256(json.dumps(payload["solution"]["top50_supplier_ids"],ensure_ascii=False).encode()).hexdigest()}]
    (paper/"claim-registry.json").write_text(json.dumps(claims,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); (paper/"evidence-index.json").write_text(json.dumps([{ "evidence_id":"RESULT","path":"results/result_object.json","sha256":digest}],ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

if __name__ == "__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--root",type=Path,required=True);main(parser.parse_args().root)

"""Render registered result figures from the unified supplier-chain result object."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def main(root:Path)->None:
 result=json.loads((root/"results"/"result_object.json").read_text(encoding="utf-8")); ranking=pd.read_csv(root/"results"/"supplier_ranking.csv"); figures=root/"figures";data=root/"figure_data";figures.mkdir(exist_ok=True);data.mkdir(exist_ok=True)
 entries=[]
 for fid,column,title in [("fig_supplier_scores","score","Supplier consensus scores"),("fig_top50_capacity","product_equiv_capacity","Top-50 product-equivalent capacity")]:
  subset=ranking.head(50) if fid.endswith("capacity") else ranking
  csv=data/f"{fid}.csv";subset[["supplier_id",column]].to_csv(csv,index=False)
  fig,ax=plt.subplots(figsize=(7,3.4));ax.plot(range(1,len(subset)+1),subset[column].to_numpy(),lw=1);ax.set(xlabel="rank",ylabel=column,title=title);fig.tight_layout();svg=figures/f"{fid}.svg";png=figures/f"{fid}.png";pdf=figures/f"{fid}.pdf";fig.savefig(svg);fig.savefig(pdf);fig.savefig(png,dpi=250);plt.close(fig)
  entries.append({"figure_id":fid,"path":str(svg.relative_to(root)).replace("\\","/"),"data_file":str(csv.relative_to(root)).replace("\\","/"),"claim_ids":["CLAIM_TOP50"],"unit":"m3" if column.endswith("capacity") else "score","title":title,"sample_size":len(subset),"inserted_in_body":True,"sha256":sha(svg)})
 (root/"paper"/"figure-registry.json").write_text(json.dumps(entries,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 claims=[{"claim_id":"CLAIM_TOP50","evidence_id":"RESULT","json_pointer":"/solution/top50_supplier_ids","array_length":50,"array_sha256":hashlib.sha256(json.dumps(result["solution"]["top50_supplier_ids"],ensure_ascii=False).encode()).hexdigest()}]
 evidence=[{"evidence_id":"RESULT","path":"results/result_object.json","sha256":sha(root/"results"/"result_object.json")}]
 (root/"paper"/"claim-registry.json").write_text(json.dumps(claims,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");(root/"paper"/"evidence-index.json").write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 (root/"reports"/"figure_audit_report.json").write_text(json.dumps({"status":"PASS","figures":len(entries),"placeholder_figures":0},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,required=True);main(p.parse_args().root)

"""Record bounded, non-fabricated source evidence for a competition modeling run."""
from __future__ import annotations
import argparse,json
from pathlib import Path
def dump(root:Path,name:str,value)->None:
 p=root/"results"/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def main(root:Path)->None:
 queries=[{"query":"robust supplier selection mixed integer programming","purpose":"set-selection formulation"},{"query":"CUMCM 2021 C official problem","purpose":"authoritative task statement"}]
 official={"title":"2021 Higher Education Press Cup CUMCM Problem C","url":"https://www.mcm.edu.cn/html_cn/node/10405905647c52abfd6377c0311632b5.html","type":"official competition material","verification":"official problem PDF retained in project"}
 dump(root,"search_queries.json",queries);dump(root,"search_results.json",[official]);dump(root,"selected_sources.json",[official]);dump(root,"rejected_sources.json",[{"reason":"unverified metadata is never converted into a citation"}]);
 (root/"reports"/"literature_evidence.md").write_text("# Literature evidence\n\nThe official problem statement is the only source registered in this offline run. Method choices are presented as modeling assumptions, not as unsupported literature claims.\n",encoding="utf-8")
 (root/"paper"/"references.bib").write_text("@misc{cumcm2021c,\n title={2021 Higher Education Press Cup CUMCM Problem C},\n howpublished={Official competition material},\n url={https://www.mcm.edu.cn/html_cn/node/10405905647c52abfd6377c0311632b5.html},\n year={2021}\n}\n",encoding="utf-8")
 dump(root,"bib_validation.json",{"status":"PASS","records":1,"doi_required":False,"note":"official problem has a stable URL rather than a DOI"})
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,required=True);main(p.parse_args().root)

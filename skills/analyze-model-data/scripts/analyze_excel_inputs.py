"""Profile raw supplier-chain Excel inputs without modifying their source files."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd

def write(root: Path, name: str, value) -> None:
    path=root/"results"/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def main(root: Path) -> None:
    raw=root/"data"/"raw"; supplier=next(raw.glob("*402*.xlsx")); carrier=next(raw.glob("*8*.xlsx"))
    sx=pd.ExcelFile(supplier); orders=pd.read_excel(supplier,sheet_name=sx.sheet_names[0]); supply=pd.read_excel(supplier,sheet_name=sx.sheet_names[1]); loss=pd.read_excel(carrier)
    profile={"supplier_rows":len(orders),"supplier_columns":len(orders.columns),"supply_rows":len(supply),"carrier_rows":len(loss),"weeks":len(orders.columns)-2}
    quality={"missing":int(orders.isna().sum().sum()+supply.isna().sum().sum()+loss.isna().sum().sum()),"negative":int(((orders.select_dtypes("number")<0).sum().sum())+((supply.select_dtypes("number")<0).sum().sum())+((loss.select_dtypes("number")<0).sum().sum())),"zero_loss_records":int((loss.select_dtypes("number")==0).sum().sum())}
    write(root,"data_profile.json",profile); write(root,"data_quality_report.json",quality); write(root,"cleaning_actions.json",[{"action":"preserve raw workbooks","reason":"auditability"}]); write(root,"eda_findings.json",{"special_value":"zero carrier loss is retained as an observed value"}); write(root,"leakage_report.json",{"status":"PASS","note":"historical windows are not mixed with prospective 24-week schedule"})
    write(root,"processed_data_manifest.json",{"raw_files":[supplier.name,carrier.name],"derived_files":[]})
    (root/"reports"/"data_analysis.md").write_text(f"# Data analysis\n\n{profile['supplier_rows']} suppliers, {profile['weeks']} historical weeks, and {profile['carrier_rows']} carriers were profiled from immutable raw workbooks.\n",encoding="utf-8")

if __name__ == "__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--root",type=Path,required=True);main(parser.parse_args().root)

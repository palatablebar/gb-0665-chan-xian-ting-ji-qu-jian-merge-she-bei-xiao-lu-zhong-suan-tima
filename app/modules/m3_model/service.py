from app.modules.m2_contract.service import run as previous
from app.errors import DomainError
from .rules import partition

def run(options=None):
    result=previous(options);rows=[];partitions=[]
    for row in result["rows"]:
        try:partitions.append(partition(row));rows.append(row)
        except DomainError as exc:result["quarantine"].append({"line":row["line"],"code":exc.code,"raw":row.get("source",row)})
    result["rows"]=rows;result["partitions"]=partitions
    return result

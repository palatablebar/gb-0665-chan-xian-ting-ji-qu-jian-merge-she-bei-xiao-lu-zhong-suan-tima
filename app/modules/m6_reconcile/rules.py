from decimal import Decimal

def reconcile(result):
    items=result["results"]
    def total(key):return sum((Decimal(x[key]) for x in items),Decimal(0))
    planned,runtime,down,total_count,good=[total(k) for k in ("planned","runtime","downtime_minutes","total","good")]
    return {"planned":str(planned),"runtime":str(runtime),"downtime":str(down),"total":str(total_count),"good":str(good),"scrap":str(total_count-good),"time_ok":planned==runtime+down,"count_ok":result["input_count"]==len(result["rows"])+len(result["quarantine"])+result["blank_count"],"production_ok":good<=total_count,"exceptions":sum(x["status"]!="通过" for x in items)}

def group_lines(items):
    groups={}
    for item in items:
        bucket=groups.setdefault(item["line_id"],{"line_id":item["line_id"],"planned":Decimal(0),"runtime":Decimal(0),"downtime_minutes":Decimal(0),"total":Decimal(0),"good":Decimal(0)})
        for key in ("planned","runtime","downtime_minutes","total","good"):bucket[key]+=Decimal(item[key])
    return [{k:str(v) for k,v in row.items()} for row in groups.values()]

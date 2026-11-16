from decimal import Decimal

def reconcile(result):
    items=result["results"]
    def total(key):return sum((Decimal(x[key]) for x in items),Decimal(0))
    planned,runtime,down,total_count,good=[total(k) for k in ("planned","runtime","downtime_minutes","total","good")]
    tagged=sum((Decimal(s["minutes"]) for p in result["partitions"] for s in p["segments"] if s.get("order")),Decimal(0))
    event_minutes=sum((Decimal(e["minutes"]) for e in result.get("events",[])),Decimal(0))
    return {"planned":str(planned),"runtime":str(runtime),"downtime":str(down),"total":str(total_count),"good":str(good),"scrap":str(total_count-good),"time_ok":planned==runtime+down,"count_ok":result["input_count"]==len(result["rows"])+len(result["quarantine"])+result["blank_count"],"production_ok":good<=total_count,"exceptions":sum(x["status"]!="通过" for x in items),"events":len(result.get("events",[])),"event_minutes":str(event_minutes),"event_ok":tagged==event_minutes}

def group_lines(items,events=None):
    groups={}
    def bucket(key):return groups.setdefault(key,{"line_id":key,"planned":Decimal(0),"runtime":Decimal(0),"downtime_minutes":Decimal(0),"total":Decimal(0),"good":Decimal(0),"event_minutes":Decimal(0),"events":0})
    for item in items:
        target=bucket(item["line_id"])
        for key in ("planned","runtime","downtime_minutes","total","good"):target[key]+=Decimal(item[key])
    for event in events or []:
        target=bucket(event["line_id"]);target["event_minutes"]+=Decimal(event["minutes"]);target["events"]+=1
    return [{k:str(v) for k,v in row.items()} for row in groups.values()]

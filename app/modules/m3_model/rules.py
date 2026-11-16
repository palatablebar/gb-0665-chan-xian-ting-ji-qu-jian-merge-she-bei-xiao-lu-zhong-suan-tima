from decimal import Decimal
from app.modules.m2_contract.service import parse_instant as instant
from app.errors import reject
PRIORITY={"safety":3,"fault":2,"setup":1}

def clip(pair,start,end):
    if not isinstance(pair,(list,tuple)) or len(pair)!=2:reject("INTERVAL","区间应为起止时间")
    left,right=instant(pair[0]),instant(pair[1])
    if right<=left:reject("INTERVAL","区间终点须晚于起点")
    return max(left,start),min(right,end)

def minutes(left,right):return Decimal(str((right-left).total_seconds()))/60

def partition(row):
    start,end=instant(row["start"]),instant(row["end"]);breaks=[];stops=[]
    for pair in row["breaks"]:
        a,b=clip(pair,start,end)
        if a<b:breaks.append((a,b))
    for stop in row["downtime"]:
        if not isinstance(stop,dict) or stop.get("cause") not in PRIORITY:reject("CAUSE","停机原因未知")
        a,b=clip(stop.get("interval"),start,end)
        if a<b:stops.append((a,b,stop["cause"]))
    bounds=sorted({start,end}|{x for pair in breaks for x in pair}|{x for a,b,_ in stops for x in (a,b)})
    planned=Decimal(0);down=Decimal(0);rest=Decimal(0);causes={k:Decimal(0) for k in PRIORITY};segments=[]
    for a,b in zip(bounds,bounds[1:]):
        duration=minutes(a,b)
        if any(l<=a and b<=r for l,r in breaks):rest+=duration;state="break"
        else:
            planned+=duration
            active={cause for l,r,cause in stops if l<=a and b<=r}
            if active:
                cause=sorted(active,key=lambda k:(-PRIORITY[k],k))[0];causes[cause]+=duration;down+=duration;state=cause
            else:state="running"
        segments.append({"start":a.isoformat(),"end":b.isoformat(),"minutes":str(duration),"state":state})
    return {"record_id":row["record_id"],"line_id":row["line_id"],"line":row["line"],"scheduled":str(minutes(start,end)),"break_minutes":str(rest),"planned":str(planned),"downtime_minutes":str(down),"runtime":str(planned-down),"causes":{k:str(v) for k,v in causes.items()},"segments":segments,"total":row["total"],"good":row["good"],"ideal_seconds":row["ideal_seconds"]}

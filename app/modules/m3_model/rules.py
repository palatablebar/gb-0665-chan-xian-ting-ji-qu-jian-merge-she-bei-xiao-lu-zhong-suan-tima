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

def winner(stops,a,b):
    covering=[s for s in stops if s[0]<=a and b<=s[1]]
    if not covering:return None
    return min(covering,key=lambda s:(-PRIORITY[s[2]],s[2],s[3] or "",s[0].isoformat(),s[1].isoformat()))

def partition(row):
    start,end=instant(row["start"]),instant(row["end"]);breaks=[];stops=[]
    for pair in row["breaks"]:
        a,b=clip(pair,start,end)
        if a<b:breaks.append((a,b))
    for stop in row["downtime"]:
        if not isinstance(stop,dict) or stop.get("cause") not in PRIORITY:reject("CAUSE","停机原因未知")
        a,b=clip(stop.get("interval"),start,end)
        if a<b:stops.append((a,b,stop["cause"],stop.get("order")))
    bounds=sorted({start,end}|{x for pair in breaks for x in pair}|{x for a,b,_,_ in stops for x in (a,b)})
    planned=Decimal(0);down=Decimal(0);rest=Decimal(0);causes={k:Decimal(0) for k in PRIORITY};segments=[]
    for a,b in zip(bounds,bounds[1:]):
        duration=minutes(a,b);order=None
        if any(l<=a and b<=r for l,r in breaks):rest+=duration;state="break"
        else:
            planned+=duration
            hit=winner(stops,a,b)
            if hit:
                cause=hit[2];order=hit[3];causes[cause]+=duration;down+=duration;state=cause
            else:state="running"
        segment={"start":a.isoformat(),"end":b.isoformat(),"minutes":str(duration),"state":state}
        if order:segment["order"]=order
        segments.append(segment)
    return {"record_id":row["record_id"],"line_id":row["line_id"],"line":row["line"],"scheduled":str(minutes(start,end)),"break_minutes":str(rest),"planned":str(planned),"downtime_minutes":str(down),"runtime":str(planned-down),"causes":{k:str(v) for k,v in causes.items()},"segments":segments,"total":row["total"],"good":row["good"],"ideal_seconds":row["ideal_seconds"]}

def link(rows,partitions):
    by_id={row["record_id"]:row for row in rows};events={}
    for row in rows:
        for entry in row["downtime"]:
            order=isinstance(entry,dict) and entry.get("order")
            if not order:continue
            fragment={"record_id":row["record_id"],"line":row["line"],"interval":entry["interval"],"cause":entry["cause"]}
            if entry.get("handover"):fragment["handover"]=entry["handover"]
            events.setdefault(order,{"order":order,"fragments":[],"slices":[]})["fragments"].append(fragment)
    for part in partitions:
        for segment in part["segments"]:
            order=segment.get("order")
            if order:events[order]["slices"].append({"record_id":part["record_id"],"start":segment["start"],"end":segment["end"],"minutes":segment["minutes"],"state":segment["state"]})
    linked=[]
    for event in events.values():
        fragments,slices=event["fragments"],event["slices"]
        start=min(instant(f["interval"][0]) for f in fragments);end=max(instant(f["interval"][1]) for f in fragments)
        owner=None
        for record_id in sorted({s["record_id"] for s in slices}):
            row=by_id[record_id]
            if instant(row["start"])<=start<instant(row["end"]):owner=record_id;break
        if owner is None and slices:owner=min(slices,key=lambda s:(s["start"],s["record_id"]))["record_id"]
        if owner is None:owner=min(fragments,key=lambda f:(instant(f["interval"][0]),f["record_id"]))["record_id"]
        tally={}
        for s in slices:tally[s["state"]]=tally.get(s["state"],Decimal(0))+Decimal(s["minutes"])
        if tally:cause=sorted(tally,key=lambda k:(-tally[k],-PRIORITY[k],k))[0]
        else:cause=min(fragments,key=lambda f:(instant(f["interval"][0]),f["record_id"]))["cause"]
        handovers=[{"record_id":f["record_id"],"line":f["line"],"text":f["handover"]} for f in fragments if f.get("handover")]
        per_shift={}
        for s in slices:per_shift[s["record_id"]]=per_shift.get(s["record_id"],Decimal(0))+Decimal(s["minutes"])
        event.update({"line_id":by_id[owner]["line_id"],"cause":cause,"owner":owner,"start":start.isoformat(),"end":end.isoformat(),"minutes":str(sum(tally.values(),Decimal(0))),"cause_conflict":len({f["cause"] for f in fragments})>1,"line_conflict":len({by_id[f["record_id"]]["line_id"] for f in fragments})>1,"handovers":handovers,"slices_text":" + ".join(f"{rid} {m}" for rid,m in per_shift.items()),"basis":"；".join(f'{f["record_id"]}#L{f["line"]} [{f["interval"][0]}→{f["interval"][1]}] {f["cause"]}' for f in fragments),"handover_text":"；".join(f'{h["record_id"]}#L{h["line"]}：{h["text"]}' for h in handovers)})
        linked.append(event)
    linked.sort(key=lambda e:(e["start"],e["order"]))
    owners={e["order"]:e["owner"] for e in linked}
    for part in partitions:
        tagged={}
        for segment in part["segments"]:
            order=segment.get("order")
            if order:tagged[order]=tagged.get(order,Decimal(0))+Decimal(segment["minutes"])
        part["orders"]=[{"order":o,"minutes":str(m),"owner":owners[o]} for o,m in sorted(tagged.items())]
        part["orders_text"]="；".join(f"{o} {m}→归属{owners[o]}" for o,m in sorted(tagged.items())) or "—"
    return linked

import unicodedata,json
from decimal import Decimal,InvalidOperation
from datetime import datetime,timezone
from app.config import SENTINELS
from app.errors import reject

def number(value):
    text=unicodedata.normalize("NFKC",str(value)).strip().replace(",","")
    if text in SENTINELS:reject("MISSING","必要值缺失")
    try:v=Decimal(text)
    except InvalidOperation:reject("VALUE","数值无效")
    if not v.is_finite():reject("VALUE","数值非有限")
    return v

def instant(text):
    try:
        value=datetime.fromisoformat(text.replace("Z","+00:00"))
        if value.tzinfo is None:raise ValueError()
        return value.astimezone(timezone.utc)
    except (ValueError,AttributeError):reject("TIME","时间须包含偏移")

def normalize(row):
    start,end=instant(row["start"]),instant(row["end"])
    if end<=start or (end-start).total_seconds()>86400:reject("TIME","班次长度无效")
    total,good,ideal=number(row["total"]),number(row["good"]),number(row["ideal_seconds"])
    if min(total,good)<0 or good>total or total%1 or good%1 or ideal<=0:reject("COUNT","产量或节拍无效")
    if not row["record_id"].strip() or not row["line_id"].strip():reject("MISSING","缺少班报编号")
    try:
        down=json.loads(row["downtime"]);breaks=json.loads(row["breaks"])
        if not isinstance(down,list) or not isinstance(breaks,list):raise ValueError()
    except (ValueError,TypeError):reject("INTERVAL","区间格式无效")
    return {**row,"source":{k:v for k,v in row.items() if k!="line"},"start":start.isoformat(),"end":end.isoformat(),"total":str(total),"good":str(good),"ideal_seconds":str(ideal),"downtime":down,"breaks":breaks}

def deduplicate(rows):
    groups={};good=[];bad=[]
    for row in rows:groups.setdefault(row["record_id"],[]).append(row)
    for items in groups.values():
        hashes={json.dumps({k:v for k,v in row.items() if k!="line"},sort_keys=True) for row in items}
        if len(hashes)>1:bad.extend({"line":x["line"],"code":"CONFLICT","raw":x} for x in items)
        else:good.append(items[0]);bad.extend({"line":x["line"],"code":"DUPLICATE","raw":x} for x in items[1:])
    return good,bad

import csv,io,json
from decimal import Decimal
import pytest
from app.modules.m3_model.service import run as model
from app.modules.m6_reconcile.service import run as reconcile
from app.modules.m7_batches.service import run as batches
from app.modules.m7_batches.rules import csv_evidence
from app.store import history

@pytest.fixture
def cross():return {"sample":"cross"}

def event(result,order="WO-7701"):return next(x for x in result["events"] if x["order"]==order)

def make_csv(*rows):
    buffer=io.StringIO();writer=csv.writer(buffer)
    writer.writerow(["record_id","line_id","start","end","total","good","ideal_seconds","downtime","breaks"])
    for row in rows:writer.writerow(row)
    return buffer.getvalue()

def shift(record_id,start,end,down,line_id="P01",breaks=None):
    return [record_id,line_id,start,end,"240","228","60",json.dumps(down,ensure_ascii=False),json.dumps(breaks or [])]

NIGHT_A="2026-11-10T22:00:00+08:00","2026-11-11T06:00:00+08:00"
NIGHT_B="2026-11-11T06:00:00+08:00","2026-11-11T14:00:00+08:00"
SPAN=["2026-11-11T05:00:00+08:00","2026-11-11T07:30:00+08:00"]

def test_event_attributed_to_start_shift(cross): # 归属=开始班，事件完整
    ev=event(model(cross))
    assert ev["owner"]=="S1101" and ev["cause"]=="fault" and ev["line_id"]=="P01"
    assert Decimal(ev["minutes"])==150
    assert ev["start"]=="2026-11-10T21:00:00+00:00" and ev["end"]=="2026-11-10T23:30:00+00:00"

def test_shift_slices_unchanged(cross): # 扣时仍按物理切片分班
    parts={p["record_id"]:p for p in model(cross)["partitions"]}
    assert Decimal(parts["S1101"]["downtime_minutes"])==90
    assert Decimal(parts["S1102"]["downtime_minutes"])==90
    assert "WO-7701 60.0→归属S1101" in parts["S1101"]["orders_text"]
    assert "WO-7701 90.0→归属S1101" in parts["S1102"]["orders_text"]

def test_event_conservation(cross):
    rec=reconcile(cross)["reconciliation"]
    assert rec["time_ok"] is True and rec["event_ok"] is True
    assert rec["events"]==1 and Decimal(rec["event_minutes"])==150

def test_line_totals_show_whole_event(cross):
    lines={x["line_id"]:x for x in reconcile(cross)["line_totals"]}
    assert Decimal(lines["P01"]["event_minutes"])==150 and lines["P01"]["events"]=="1"
    assert Decimal(lines["P02"]["event_minutes"])==0 and lines["P02"]["events"]=="0"

def test_rerun_no_double_deduction(cross): # 同一工单重跑不重复扣减
    a,b=batches(cross),batches(cross)
    assert a["manifest"]["run_id"]==b["manifest"]["run_id"] and len(history())==1
    assert Decimal(event(a)["minutes"])==150

def test_handover_preserved(cross): # 交接说明不丢失
    ev=event(model(cross))
    texts=[h["text"] for h in ev["handovers"]]
    assert any("交班" in t for t in texts) and any("接班" in t for t in texts)
    assert "S1101" in ev["handover_text"] and "S1102" in ev["handover_text"]

def test_evidence_csv_lists_event(cross):
    text=csv_evidence(batches(cross))
    assert "事件" in text and "WO-7701" in text and "交班" in text

def test_backfill_overlap_no_double(): # 补录重叠片段不重复扣减，片段与交接说明全保留
    text=make_csv(
        shift("S1101",*NIGHT_A,[{"interval":SPAN,"cause":"fault","order":"WO-7701","handover":"交班：主轴抱闸未复位"},{"interval":["2026-11-11T05:30:00+08:00","2026-11-11T08:00:00+08:00"],"cause":"fault","order":"WO-7701","handover":"补录：夜班巡检补充"}]),
        shift("S1102",*NIGHT_B,[{"interval":SPAN,"cause":"fault","order":"WO-7701","handover":"接班：07:30复位"}]))
    result=model({"text":text});ev=event(result)
    assert Decimal(ev["minutes"])==150
    assert len(ev["fragments"])==3 and len(ev["handovers"])==3
    parts={p["record_id"]:p for p in result["partitions"]}
    assert Decimal(parts["S1101"]["downtime_minutes"])==60 and Decimal(parts["S1102"]["downtime_minutes"])==90

def test_backfill_zero_slice_kept(): # 补录落在班次窗口外：不改结论、不丢记录
    text=make_csv(
        shift("S1101",*NIGHT_A,[{"interval":SPAN,"cause":"fault","order":"WO-7701","handover":"交班：主轴抱闸未复位"}]),
        shift("S1102",*NIGHT_B,[{"interval":SPAN,"cause":"fault","order":"WO-7701"}]),
        shift("S1109","2026-11-11T14:00:00+08:00","2026-11-11T22:00:00+08:00",[{"interval":SPAN,"cause":"fault","order":"WO-7701","handover":"补录：白班确认工单关闭"}]))
    ev=event(model({"text":text}))
    assert Decimal(ev["minutes"])==150 and ev["owner"]=="S1101"
    assert len(ev["fragments"])==3 and "白班确认工单关闭" in ev["handover_text"]

def test_cause_conflict_flagged(): # 同工单原因不一致：分钟多者为准并标记
    text=make_csv(
        shift("S1101",*NIGHT_A,[{"interval":SPAN,"cause":"fault","order":"WO-7701"}]),
        shift("S1102",*NIGHT_B,[{"interval":SPAN,"cause":"setup","order":"WO-7701"}]))
    ev=event(model({"text":text}))
    assert ev["cause"]=="setup" and ev["cause_conflict"] is True
    assert Decimal(ev["minutes"])==150

def test_owner_fallback_without_slice(): # 申报完全落在窗口外：归属申报班，分钟为零
    text=make_csv(shift("S1109","2026-11-11T14:00:00+08:00","2026-11-11T22:00:00+08:00",[{"interval":SPAN,"cause":"fault","order":"WO-7701","handover":"补录：事后补登"}]))
    ev=event(model({"text":text}))
    assert ev["owner"]=="S1109" and Decimal(ev["minutes"])==0 and ev["handovers"]

def test_same_shift_two_sessions_one_event(): # 同班同工单两段维修仍是一条事件
    text=make_csv(shift("S1101",*NIGHT_A,[{"interval":["2026-11-10T23:00:00+08:00","2026-11-10T23:30:00+08:00"],"cause":"fault","order":"WO-7701"},{"interval":["2026-11-11T01:00:00+08:00","2026-11-11T01:30:00+08:00"],"cause":"fault","order":"WO-7701"}]))
    result=model({"text":text})
    assert len(result["events"])==1 and Decimal(event(result)["minutes"])==60

def test_order_must_be_text():
    text=make_csv(shift("S1101",*NIGHT_A,[{"interval":SPAN,"cause":"fault","order":{"wo":1}}]))
    assert "ORDER" in [x["code"] for x in model({"text":text})["quarantine"]]

def test_handover_must_be_text():
    text=make_csv(shift("S1101",*NIGHT_A,[{"interval":SPAN,"cause":"fault","order":"WO-7701","handover":123}]))
    assert "HANDOVER" in [x["code"] for x in model({"text":text})["quarantine"]]

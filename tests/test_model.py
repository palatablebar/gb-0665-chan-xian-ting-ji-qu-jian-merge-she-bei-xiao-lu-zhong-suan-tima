from decimal import Decimal
import pytest
from app.modules.m3_model.service import run
from app.modules.m3_model.rules import partition
from app.modules.m2_contract.service import run as contract
from app.errors import DomainError

def test_overlap_union(clean):assert run(clean)["partitions"][0]["downtime_minutes"]=="90.0"
def test_planned(clean):assert Decimal(run(clean)["partitions"][0]["planned"])==450
def test_priority(clean): # TRAP-19
    assert Decimal(run(clean)["partitions"][0]["causes"]["fault"])==60
    assert Decimal(run(clean)["partitions"][0]["causes"]["setup"])==30
def test_order_invariant(clean):
    row=contract(clean)["rows"][0];a=partition(row);row["downtime"].reverse();assert partition(row)==a
def test_invalid_cause(dirty):assert "CAUSE" in [x["code"] for x in run(dirty)["quarantine"]]
def test_half_open(clean): # TRAP-23
    segments=run(clean)["partitions"][0]["segments"];assert sum((Decimal(x["minutes"]) for x in segments),Decimal(0))==480
def test_break_overlap_once(clean):
    row=contract(clean)["rows"][0];row["breaks"]*=2;assert Decimal(partition(row)["break_minutes"])==30

def test_cross_midnight(clean):
    row=contract(clean)["rows"][0]
    row.update(start="2026-11-01T22:00:00+08:00",end="2026-11-02T06:00:00+08:00",breaks=[["2026-11-02T02:00:00+08:00","2026-11-02T02:30:00+08:00"]],downtime=[{"interval":["2026-11-01T23:00:00+08:00","2026-11-02T01:00:00+08:00"],"cause":"fault"}])
    result=partition(row)
    assert Decimal(result["planned"])==450
    assert Decimal(result["downtime_minutes"])==120
    assert Decimal(result["runtime"])==330

from decimal import Decimal
from app.modules.m4_calculate.service import run
from app.modules.m4_calculate.rules import efficiency

def test_availability(clean):assert Decimal(run(clean)["results"][0]["availability"])==Decimal("0.8")
def test_performance(clean):assert Decimal(run(clean)["results"][0]["performance"])==Decimal(5)/6
def test_quality(clean):assert Decimal(run(clean)["results"][0]["quality"])==Decimal("0.95")
def test_oee(clean): # TRAP-10
    assert Decimal(run(clean)["results"][0]["oee"])==Decimal(285)/450
def test_no_schedule(clean):
    item=run(clean)["partitions"][0];item.update(planned="0",runtime="0",total="0",good="0");assert efficiency(item)["status"]=="无计划"
def test_overproduction(clean):
    item=run(clean)["partitions"][0];item.update(ideal_seconds="120");assert efficiency(item)["status"]=="超产"
def test_zero_production(clean):
    item=run(clean)["partitions"][0];item.update(total="0",good="0");assert efficiency(item)["oee"]=="0"

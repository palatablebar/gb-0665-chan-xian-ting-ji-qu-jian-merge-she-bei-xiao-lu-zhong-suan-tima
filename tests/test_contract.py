from decimal import Decimal
import pytest
from app.modules.m2_contract.service import run
from app.modules.m2_contract.rules import number,instant,deduplicate
from app.errors import DomainError

def test_numbers(clean):assert run(clean)["rows"][0]["total"]=="300"
def test_fullwidth(): # TRAP-06
    assert number("１，２３４")==1234
def test_sentinel(dirty): # TRAP-07
    assert "MISSING" in [x["code"] for x in run(dirty)["quarantine"]]
def test_bad_production(dirty):assert "COUNT" in [x["code"] for x in run(dirty)["quarantine"]]
def test_bad_time(dirty):assert "TIME" in [x["code"] for x in run(dirty)["quarantine"]]
def test_timezone(): # TRAP-11
    assert instant("2026-11-01T08:00:00+08:00")==instant("2026-11-01T00:00:00Z")
def test_conflict(clean): # TRAP-14
    a=run(clean)["rows"][0];good,bad=deduplicate([a,{**a,"total":"500","line":99}]);assert good==[];assert len(bad)==2

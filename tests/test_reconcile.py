from decimal import Decimal
from app.modules.m6_reconcile.service import run

def test_planned(clean):assert Decimal(run(clean)["reconciliation"]["planned"])==16200
def test_runtime(clean):assert Decimal(run(clean)["reconciliation"]["runtime"])==12960
def test_downtime(clean):assert Decimal(run(clean)["reconciliation"]["downtime"])==3240
def test_production(clean):assert run(clean)["reconciliation"]["good"]=="10260"
def test_time_invariant(dirty):assert run(dirty)["reconciliation"]["time_ok"] is True
def test_count_invariant(dirty):assert run(dirty)["reconciliation"]["count_ok"] is True
def test_line_groups(clean):assert len(run(clean)["line_totals"])==6

import pytest
from app.modules.m5_quarantine.service import run
from app.modules.m5_quarantine.rules import distribution,select,evidence
from app.errors import DomainError

def test_reason_counts(dirty):assert run(dirty)["reason_counts"]=={"CAUSE":1,"COUNT":1,"DUPLICATE":1,"MISSING":1,"TIME":1}
def test_clean(clean):assert run(clean)["reason_counts"]=={}
def test_complete(dirty):assert run(dirty)["evidence_complete"] is True
def test_select(dirty):assert len(select(run(dirty)["quarantine"],"COUNT"))==1
def test_all(dirty):assert len(select(run(dirty)["quarantine"]))==5
def test_unknown(dirty):
    with pytest.raises(DomainError):select(run(dirty)["quarantine"],"WRONG")
def test_missing_evidence():assert evidence([{"code":"MISSING"}]) is False

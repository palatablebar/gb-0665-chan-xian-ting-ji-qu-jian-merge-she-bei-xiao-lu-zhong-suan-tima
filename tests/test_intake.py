import pytest
from app.modules.m1_intake.service import run
from app.modules.m1_intake.rules import read
from app.errors import DomainError

def test_dirty(dirty):assert run(dirty)["input_count"]==41
def test_clean(clean):assert len(run(clean)["rows"])==36
def test_bom(dirty): # TRAP-02
    assert run(dirty)["rows"][0]["record_id"]=="S0101"
def test_encoding(): # TRAP-01
    assert run({"sample":"gb18030"})["encoding"]=="gb18030"
def test_source_lines(dirty):assert run(dirty)["rows"][0]["line"]==2
def test_empty():
    with pytest.raises(DomainError,match="文件为空"):read(b"")
def test_unknown():
    with pytest.raises(DomainError):run({"sample":"wrong"})

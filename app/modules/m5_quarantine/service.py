from app.modules.m3_model.service import run as previous
from .rules import distribution,evidence

def summarize(result):
    result["reason_counts"]=distribution(result["quarantine"])
    result["evidence_complete"]=evidence(result["quarantine"])
    return result

def run(options=None):
    return summarize(previous(options))

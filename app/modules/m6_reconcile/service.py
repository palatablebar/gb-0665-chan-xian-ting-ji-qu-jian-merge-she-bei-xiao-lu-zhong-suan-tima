from app.modules.m4_calculate.service import run as previous
from app.modules.m5_quarantine.service import summarize
from .rules import reconcile,group_lines

def run(options=None):
    result=previous(options);result["reconciliation"]=reconcile(result);result["line_totals"]=group_lines(result["results"])
    summarize(result)
    return result

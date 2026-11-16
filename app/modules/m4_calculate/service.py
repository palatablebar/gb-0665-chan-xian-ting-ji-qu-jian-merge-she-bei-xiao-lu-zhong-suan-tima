from app.modules.m3_model.service import run as previous
from .rules import efficiency

def run(options=None):
    result=previous(options);result["results"]=[efficiency(x) for x in result["partitions"]]
    return result

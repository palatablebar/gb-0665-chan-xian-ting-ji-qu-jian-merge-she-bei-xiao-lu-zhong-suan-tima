from pathlib import Path
import os
TITLE='产线效率运行台'
RULE_VERSION="2026.11.2"
SAMPLE_DIR=Path(__file__).resolve().parent.parent/"sample_data"
MODULES=[('intake', '班报采信'), ('contract', '班次契约'), ('model', '停机裁决'), ('calculate', '效率重算'), ('quarantine', '缺陷隔离'), ('reconcile', '班次对账'), ('batches', '运行复核')]
SENTINELS={"", "-", "N/A", "NULL", "未知"}
def data_dir():
    return Path(os.environ.get("DATA_DIR", "./var"))

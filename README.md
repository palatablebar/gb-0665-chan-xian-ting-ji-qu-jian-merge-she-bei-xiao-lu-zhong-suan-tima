# 产线停机裁决与效率重算

班次按休息与停机所有端点切片，先扣休息并集，再按安全、故障、换型优先级分配停机。OEE使用未舍入的三因子计算，并保留超产异常。

使用者按采信、规则复算、异常复核和归档顺序处理一批数据。启动后自动装入异常样例，切换基准样例可比较两者结论。

## 启动与测试
```sh
docker compose up --build -d
docker compose exec -T app pytest -q
docker compose config --quiet
```

浏览器打开 [工作台](http://localhost:18204)。

## 业务模块

- 班报采信：导入班报并保留物理行号，入口 `/intake` 与 `GET /api/intake`。
- 班次契约：规范数量、节拍与偏移时间，入口 `/contract` 与 `GET /api/contract`。
- 停机裁决：裁剪并合并重叠区间，入口 `/model` 与 `GET /api/model`。
- 效率重算：复算三项效率及OEE，入口 `/calculate` 与 `GET /api/calculate`。
- 缺陷隔离：按原因筛查异常班报，入口 `/quarantine` 与 `GET /api/quarantine`。
- 班次对账：核查时间与产量守恒，入口 `/reconcile` 与 `GET /api/reconcile`。
- 运行复核：保存运行与版本复核，入口 `/batches` 与 `GET /api/batches`。

## 演示
选择样例后运行，核对业务结论与来源行。异常行保留原值和原因码。复核提交使用当前版本；旧版本返回 409。CSV证据只保留一个归档入口。

## API
- `POST /api/runs`：JSON 中可指定 `sample`、`text` 与 `params`。
- `POST /api/runs/{run_id}/review`：提交 `revision`、`decision`。
- `GET /api/runs/{run_id}/evidence.csv`：来源证据。
- `GET /docs`：接口定义。

## 数据保存
SQLite 位于命名卷 records。相同内容、参数与规则版本只产生一条运行记录。仅需重启时执行 `docker compose restart app`。要重新初始化样例数据，先备份所需记录，再执行 `docker compose down -v` 与 `docker compose up --build -d`；此操作会删除当前项目的历史与复核数据。

## 定义与边界
计划分钟=运行分钟+有效停机分钟。班次总分钟=计划分钟+休息并集分钟。总产=良品+废品。起止时间使用含偏移的ISO格式，班次最长24小时。区间采用[start,end)，超出班次的停机裁剪，重叠休息只扣一次。total与good为整数件，ideal_seconds为每件理想秒数。零计划、零运行、零产量分别给出状态，不以任意分母补零。

## 已知不覆盖
不推断缺失班报，不接入PLC。样例按班次隔离计算，不自动分割换产品后的节拍；混产品需分别生成班报。

## 目录
`app/modules/` 为七个业务模块，`sample_data/` 提供基准与异常台账，`tests/` 包含模块测试与端到端测试，`docs/` 保存定义与深度登记。

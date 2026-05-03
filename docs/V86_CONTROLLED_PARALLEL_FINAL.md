# V86 受控并行执行层定型版

## 定型名称

V86 = V85 具身待接入态 + 受控并行执行层。

## 核心原则

1. 低风险任务并行：分析、检索、生成、仿真、验证、草稿、mock、noop、test。
2. 高风险动作不并行：支付、签约、转账、外发、公开发布、删除、物理致动、设备启停。
3. 端侧动作强串行：手机端、日历真实写入、联系人真实写入、闹钟、设备、本地 OS 动作。
4. 所有真实执行继续复用原 `_execute_step`，不绕开 retry / fallback / rollback / checkpoint / audit。
5. 并行结果按拓扑顺序稳定回写，支持审计回放。

## 修改文件

- `orchestration/workflow/workflow_engine.py`
- `orchestration/workflow/parallel_policy.py`
- `orchestration/workflow/parallel_executor.py`
- `orchestration/state/workflow_event_store.py`

## 新增测试

- `tests/test_workflow_controlled_parallel.py`
- `tests/test_workflow_parallel_commit_barrier.py`
- `tests/test_workflow_parallel_serial_lane.py`
- `tests/test_workflow_parallel_deterministic_replay.py`

## 验收命令

```bash
pytest tests/test_workflow_controlled_parallel.py \
       tests/test_workflow_parallel_commit_barrier.py \
       tests/test_workflow_parallel_serial_lane.py \
       tests/test_workflow_parallel_deterministic_replay.py -q
```

## 一键替换方式

把本包解压到项目根目录，覆盖同名文件即可。覆盖前建议自动备份。

Linux / Mac:

```bash
bash install_v86_controlled_parallel.sh /path/to/project
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File install_v86_controlled_parallel.ps1 -ProjectRoot "C:\path\to\project"
```

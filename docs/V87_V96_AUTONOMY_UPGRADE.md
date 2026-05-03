# V87-V96 自治代理十连升级说明

本包一次性推进 10 个完整大功能：

| 版本 | 功能 | 模块 |
|---|---|---|
| V87 | 个体化长期记忆内核 | `core/autonomy/memory_kernel.py` |
| V88 | 世界接口 / Connector 注册层 | `core/autonomy/world_interface.py` |
| V89 | 能力缺口识别器 | `core/autonomy/capability_gap.py` |
| V90 | 受控能力自扩展沙箱 | `core/autonomy/extension_sandbox.py` |
| V91 | 审批中断 / Human-in-the-loop | `core/autonomy/approval_interrupt.py` |
| V92 | Trace / Audit 追踪审计 | `core/autonomy/trace_audit.py` |
| V93 | 结果质量评估器 | `core/autonomy/quality_evaluator.py` |
| V94 | 策略进化器 | `core/autonomy/strategy_evolver.py` |
| V95 | 长期/持续任务运行登记器 | `core/autonomy/continuous_task_runner.py` |
| V96 | 自治总控编排器 | `core/autonomy/autonomy_orchestrator.py` |

执行命令：

```bash
unzip -o pigeon_king_v87_v96_autonomy_upgrade.zip -d . && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v87_v96_apply_autonomy_upgrade.py && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v87_v96_verify_autonomy_upgrade.py
```

成功标志：

```text
PASS: V87-V96 autonomy upgrade verification passed.
```

安全边界：

- 不自动安装未知代码。
- 不自动发送外部消息。
- 不自动支付、删除、转账、泄露隐私。
- 高风险动作统一进入审批中断。
- 能力扩展必须先 proposal，再 sandbox evaluation，再 promotion。

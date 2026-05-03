# V97-V106 个人操作系统级治理层十连升级

这组版本接在 V87-V96 自治内核之后，目标是把“小艺”推进到更接近“个人操作系统级 AI”的治理层。

| 版本 | 大功能 | 模块 |
|---|---|---|
| V97 | 个人法典 / Constitution Kernel | `core/operating_agent/constitution_kernel.py` |
| V98 | 权限金库 / Permission Vault | `core/operating_agent/permission_vault.py` |
| V99 | Connector 市场与可信目录 | `core/operating_agent/connector_catalog.py` |
| V100 | MCP Server 管理层 | `core/operating_agent/mcp_manager.py` |
| V101 | 插件沙箱与晋升门禁 | `core/operating_agent/plugin_sandbox.py` |
| V102 | 专家 Agent 交接机制 | `core/operating_agent/specialist_handoff.py` |
| V103 | 多 Agent 协同与共识计划 | `core/operating_agent/multi_agent_coordinator.py` |
| V104 | 恢复账本 / checkpoint / rollback | `core/operating_agent/recovery_ledger.py` |
| V105 | 自治能力评测基准 | `core/operating_agent/evaluation_benchmark.py` |
| V106 | 发布治理 / Release Gate | `core/operating_agent/release_governor.py` |

执行命令：

```bash
unzip -o pigeon_king_v97_v106_operating_agent_upgrade.zip -d . && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v97_v106_apply_operating_agent_upgrade.py && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v97_v106_verify_operating_agent_upgrade.py
```

成功标志：

```text
PASS: V97-V106 operating agent upgrade verification passed.
```

安全边界：

- 涉及外部发送、支付、安装、密钥、删除，必须走 Constitution + Permission。
- 插件不能野蛮安装，必须 sandbox report 通过。
- MCP 只做注册、握手、允许工具列表，不直接执行危险动作。
- Release Gate 不通过时，不能晋升为稳定能力。

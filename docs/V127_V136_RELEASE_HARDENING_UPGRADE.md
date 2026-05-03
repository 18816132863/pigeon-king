# V127-V136 生产落地硬化层十连升级

这组版本接在 V117-V126 统一操作脊柱之后，目标是把系统从“可运行”推进到“可发布、可回滚、可验收”。

| 版本 | 大功能 | 模块 |
|---|---|---|
| V127 | 环境医生 / Environment Doctor | `core/release_hardening/environment_doctor.py` |
| V128 | 配置契约 / Config Contract | `core/release_hardening/config_contract.py` |
| V129 | 依赖守卫 / Dependency Guard | `core/release_hardening/dependency_guard.py` |
| V130 | 快照管理 / Snapshot Manager | `core/release_hardening/snapshot_manager.py` |
| V131 | 回滚计划 / Rollback Manager | `core/release_hardening/rollback_manager.py` |
| V132 | 回归矩阵 / Regression Matrix | `core/release_hardening/regression_matrix.py` |
| V133 | 发布清单 / Release Manifest | `core/release_hardening/release_manifest.py` |
| V134 | 部署档位 / Deployment Profile | `core/release_hardening/deployment_profile.py` |
| V135 | 运行报告 / Runtime Report | `core/release_hardening/runtime_report.py` |
| V136 | 发布硬化总控 / Release Hardening Kernel | `core/release_hardening/release_hardening_kernel.py` |

执行命令：

```bash
unzip -o pigeon_king_v127_v136_release_hardening_upgrade.zip -d . && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v127_v136_apply_release_hardening_upgrade.py && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v127_v136_verify_release_hardening_upgrade.py
```

成功标志：

```text
PASS: V127-V136 release hardening upgrade verification passed.
```

这组解决：

- 覆盖前先检查环境、配置、依赖。
- 覆盖前生成轻量快照 manifest。
- 自动生成回滚计划。
- 发布清单记录模块、脚本、测试、文档。
- 本地/开发/灰度/生产不同门禁。
- 最终输出可读运行报告。

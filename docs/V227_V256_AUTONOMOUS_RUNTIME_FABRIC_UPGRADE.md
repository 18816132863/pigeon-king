# V227-V256 自愈运行织网层三十连升级

这组版本接在 V197-V226 生产控制平面之后，目标是把系统升级为可发现、可编排、可自愈、可签名、可回放、可降级的运行织网。

| 版本 | 大功能 | 模块 |
|---|---|---|
| V227 | 控制塔 | `core/autonomous_runtime_fabric/v227_control_tower.py` |
| V228 | 运行 Mesh 注册表 | `core/autonomous_runtime_fabric/v228_runtime_mesh_registry.py` |
| V229 | 服务发现 | `core/autonomous_runtime_fabric/v229_service_discovery.py` |
| V230 | 配置覆盖管理器 | `core/autonomous_runtime_fabric/v230_config_overlay_manager.py` |
| V231 | 密钥引用金库 | `core/autonomous_runtime_fabric/v231_secret_reference_vault.py` |
| V232 | 策略执行点 | `core/autonomous_runtime_fabric/v232_policy_enforcement_point.py` |
| V233 | 工具经纪人 | `core/autonomous_runtime_fabric/v233_tool_broker.py` |
| V234 | 工作流模板注册表 | `core/autonomous_runtime_fabric/v234_workflow_template_registry.py` |
| V235 | 执行租约管理器 | `core/autonomous_runtime_fabric/v235_execution_lease_manager.py` |
| V236 | 状态检查点图 | `core/autonomous_runtime_fabric/v236_state_checkpoint_graph.py` |
| V237 | 回放实验室 | `core/autonomous_runtime_fabric/v237_replay_lab.py` |
| V238 | 确定性验证器 | `core/autonomous_runtime_fabric/v238_deterministic_verifier.py` |
| V239 | 自愈规划器 | `core/autonomous_runtime_fabric/v239_self_healing_planner.py` |
| V240 | 降级控制器 | `core/autonomous_runtime_fabric/v240_degradation_controller.py` |
| V241 | 告警路由器 | `core/autonomous_runtime_fabric/v241_alert_router.py` |
| V242 | 信任区管理器 | `core/autonomous_runtime_fabric/v242_trust_zone_manager.py` |
| V243 | 产物签名器 | `core/autonomous_runtime_fabric/v243_artifact_signer.py` |
| V244 | 依赖锁文件生成器 | `core/autonomous_runtime_fabric/v244_dependency_lockfile_builder.py` |
| V245 | 缓存协调器 | `core/autonomous_runtime_fabric/v245_cache_coordinator.py` |
| V246 | 队列分片规划器 | `core/autonomous_runtime_fabric/v246_queue_shard_planner.py` |
| V247 | 资源预测引擎 | `core/autonomous_runtime_fabric/v247_resource_forecast_engine.py` |
| V248 | 模型舰队管理器 | `core/autonomous_runtime_fabric/v248_model_fleet_manager.py` |
| V249 | 记忆分层管理器 | `core/autonomous_runtime_fabric/v249_memory_tier_manager.py` |
| V250 | 证据包构建器 | `core/autonomous_runtime_fabric/v250_evidence_bundle_builder.py` |
| V251 | 运行回放导出器 | `core/autonomous_runtime_fabric/v251_run_replay_exporter.py` |
| V252 | 操作员控制台 | `core/autonomous_runtime_fabric/v252_operator_console.py` |
| V253 | 集成冒烟测试 | `core/autonomous_runtime_fabric/v253_integration_smoke_test.py` |
| V254 | 安全态势复核 | `core/autonomous_runtime_fabric/v254_security_posture_review.py` |
| V255 | 织网就绪委员会 | `core/autonomous_runtime_fabric/v255_fabric_readiness_board.py` |
| V256 | 自愈运行织网总控 | `core/autonomous_runtime_fabric/v256_autonomous_runtime_fabric_kernel.py` |

执行命令：

```bash
unzip -o pigeon_king_v227_v256_autonomous_runtime_fabric_upgrade.zip -d . && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v227_v256_apply_autonomous_runtime_fabric_upgrade.py && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v227_v256_verify_autonomous_runtime_fabric_upgrade.py
```

成功标志：

```text
PASS: V227-V256 autonomous runtime fabric upgrade verification passed.
```

安全边界：

- 密钥金库只保存 reference，不保存 raw secret。
- 策略执行点会阻断 token / secret / 密钥外泄。
- 高风险动作只进入审批/降级/回放链，不直接产生真实副作用。
- 产物签名、确定性验证、回放实验室和证据包用于稳定验收。

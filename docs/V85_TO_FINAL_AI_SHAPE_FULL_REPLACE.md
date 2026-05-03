# V85 到最终 AI 形态完整覆盖包

这个包不是继续堆单独版本，而是把 V85–V316 的升级包整合后，新增 `AI_SHAPE_CORE` 主链，收束成最终 AI 形态。

## 最终主入口

- `core/ai_shape_core/AIShapeCore`
- `core/ai_shape_core/YuanLingSystem`
- `agent_kernel/ai_shape_core.py`
- `yuanling_system.py`

## 最终 AI 形态的主链

```text
用户一句话
→ GoalStrategyKernel 目标/策略契约
→ UnifiedMemoryKernel 记忆上下文
→ ConstitutionJudge 法典裁判
→ WorldInterface 世界接口能力清单
→ CapabilityExpansionKernel 能力缺口与沙箱扩展方案
→ TaskGraphEngine DAG / checkpoint / approval / recovery
→ Completion Report + Memory Writeback
```

## 执行命令

```bash
tar -xzf pigeon_king_v85_to_final_ai_shape_full_replace.tar.gz -C . && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v85_to_final_ai_shape_apply_full.py && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v85_to_final_ai_shape_verify.py
```

或 ZIP：

```bash
unzip -o pigeon_king_v85_to_final_ai_shape_full_replace.zip -d . && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v85_to_final_ai_shape_apply_full.py && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v85_to_final_ai_shape_verify.py
```

## 成功标志

```text
PASS: V85-to-final AI shape verification passed.
```

## 验收重点

最终验收不再只看 import 是否成功，而是看一次输入能否得到：

1. 目标树
2. 任务图 DAG
3. 信息源清单
4. 风险分类
5. 自动执行部分
6. 等待审批部分
7. checkpoint
8. 执行结果
9. 失败恢复方案
10. 记忆回写记录

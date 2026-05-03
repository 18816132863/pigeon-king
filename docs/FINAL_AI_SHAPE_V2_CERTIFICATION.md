# FINAL AI SHAPE V2 认证层

这版不是继续堆版本号，而是在当前 V23.1 / V85-to-final 包上增加最终形态认证层。

新增能力：

1. `AIShapeFinalizer`：最终 AI 形态认证器
2. `GoldenPathSuite`：真实黄金路径测试，不再只测 import
3. `LegacyModuleAdapter`：检查 V85–V316 模块是否被统一主链吸收
4. `ShapeScorecard`：按目标内核、记忆内核、法典裁判、世界接口、DAG、执行、能力扩展、恢复、学习、黄金路径评分
5. `scripts/ai_shape_main.py`：统一 CLI 主入口
6. `scripts/final_ai_shape_verify_v2.py`：最终形态验收脚本

## 执行命令

```bash
tar -xzf pigeon_king_final_ai_shape_v2_full_replace.tar.gz -C . && PYTHONDONTWRITEBYTECODE=1 python -S scripts/final_ai_shape_apply_v2.py && PYTHONDONTWRITEBYTECODE=1 python -S scripts/final_ai_shape_verify_v2.py
```

## 成功标志

```text
PASS: Final AI shape V2 verification passed.
```

## 现在真正验收什么

不是验收有没有模块，而是验收：

- 一句话能否进入唯一主入口
- 能否生成 GoalContract
- 能否生成目标树
- 能否生成任务 DAG
- 能否做风险裁判
- 能否阻断密钥外泄
- 能否让外部副作用等待审批
- 能否生成 checkpoint 和恢复计划
- 能否记录 memory writeback
- 能否通过多条黄金路径

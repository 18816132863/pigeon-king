# V157-V166 个体化学习层十连升级

这组版本接在 V147-V156 现实执行桥接层之后，目标是让系统越来越像用户本人。

| 版本 | 大功能 | 模块 |
|---|---|---|
| V157 | 用户画像模型 | `core/personalization/user_profile.py` |
| V158 | 偏好规则引擎 | `core/personalization/preference_rules.py` |
| V159 | 项目记忆注册表 | `core/personalization/project_memory.py` |
| V160 | 关系上下文图谱 | `core/personalization/relationship_context.py` |
| V161 | 做事流程库 | `core/personalization/procedure_library.py` |
| V162 | 决策模式学习器 | `core/personalization/decision_pattern_learner.py` |
| V163 | 反馈训练器 | `core/personalization/feedback_trainer.py` |
| V164 | 个体化漂移保护 | `core/personalization/personalization_drift_guard.py` |
| V165 | 个体化评分卡 | `core/personalization/personalization_scorecard.py` |
| V166 | 个体化学习总控 | `core/personalization/personalization_kernel.py` |

执行命令：

```bash
unzip -o pigeon_king_v157_v166_personalization_upgrade.zip -d . && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v157_v166_apply_personalization_upgrade.py && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v157_v166_verify_personalization_upgrade.py
```

成功标志：

```text
PASS: V157-V166 personalization upgrade verification passed.
```

这组解决：

- 记住用户喜欢“一次性压缩包 + 一条命令”。
- 记住用户不喜欢一点点修。
- 区分技术执行人、直播运营团队等不同关系对象。
- 将版本推进、高风险审批等做成可复用流程。
- 反馈不会直接污染长期偏好，先过漂移保护。

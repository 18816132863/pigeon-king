# V83.0 人格与记忆回滚态

目标：允许系统越用越像用户，但禁止记忆污染、人格漂移、策略越权。

新增：
- PersonaMemoryAuditor
- MemorySnapshot
- 敏感记忆阻断
- 策略覆盖记忆阻断
- drift scan 与 rollback plan

不变量：
- 记忆不能覆盖支付/签署/物理等硬法典。
- 人格进化必须可审查、可回滚。

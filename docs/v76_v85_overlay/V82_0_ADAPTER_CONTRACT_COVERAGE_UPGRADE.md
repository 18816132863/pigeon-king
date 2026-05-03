# V82.0 接口契约覆盖态

目标：让未来真实接入只剩 adapter / credential / approval config，而不是重写主脑。

新增：
- AdapterContractGate
- payment / signature / physical / identity / destructive / external_send 全部 mock contract
- MCP / connector / device / robot / payment 合同覆盖检查

不变量：
- mock adapter 存在
- live adapter 可声明
- credential 不绑定
- live_enabled = false

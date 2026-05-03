# V81.0 权限租约与双钥审批态

目标：把“拥有全部权限的能力设计”改成可审计的权限租约，而不是裸 root 权限。

新增：
- PermissionLeaseManager
- default pending-access lease
- commit 类动作双钥审批 envelope
- 支付/签署/物理/外发/破坏性动作不因权限存在而放行

不变量：
- 权限可建模，但 live commit 不开启。
- commit 动作只能形成审批包，不能真实执行。

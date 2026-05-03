from __future__ import annotations

from .schemas import ActionSpec, ActionKind, ActionRisk, ActionStatus, new_id


class ActionDSLCompiler:
    """V147: compile natural goal into a bounded action spec."""

    def compile(self, goal: str) -> ActionSpec:
        if any(x in goal for x in ["转账", "付款", "支付", "打款"]):
            kind = ActionKind.PAY
            risk = ActionRisk.L4
            target = "payment"
            reversible = False
        elif any(x in goal for x in ["删除", "清空", "覆盖"]):
            kind = ActionKind.DELETE
            risk = ActionRisk.L4
            target = "file_or_data"
            reversible = False
        elif any(x in goal for x in ["发送", "发给客户", "发邮件", "群发"]):
            kind = ActionKind.SEND
            risk = ActionRisk.L3
            target = "external_message"
            reversible = False
        elif any(x in goal for x in ["安装", "插件", "pip install", "下载执行"]):
            kind = ActionKind.INSTALL
            risk = ActionRisk.L4
            target = "extension"
            reversible = True
        elif any(x in goal for x in ["手机", "电脑", "设备", "点击", "打开应用"]):
            kind = ActionKind.DEVICE_CONTROL
            risk = ActionRisk.L3
            target = "device"
            reversible = True
        elif any(x in goal for x in ["图片", "视频", "海报", "logo"]):
            kind = ActionKind.MEDIA_GENERATE
            risk = ActionRisk.L1
            target = "media"
            reversible = True
        elif any(x in goal for x in ["写入", "修改", "保存", "覆盖包"]):
            kind = ActionKind.WRITE
            risk = ActionRisk.L2
            target = "workspace"
            reversible = True
        elif any(x in goal for x in ["查", "读取", "总结", "分析"]):
            kind = ActionKind.READ
            risk = ActionRisk.L0
            target = "information"
            reversible = True
        else:
            kind = ActionKind.PLAN_ONLY
            risk = ActionRisk.L1
            target = "plan"
            reversible = True

        requires_approval = risk in {ActionRisk.L3, ActionRisk.L4}
        return ActionSpec(
            id=new_id("action"),
            goal=goal,
            kind=kind,
            risk=risk,
            target=target,
            parameters={"raw_goal": goal},
            reversible=reversible,
            requires_approval=requires_approval,
            status=ActionStatus.COMPILED,
        )

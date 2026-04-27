这是 V23.1 到 V65.0 的完整替换包，不是增量包。

解压后进入项目根目录：
cd pigeon_king_v10_9

先跑完整替换门禁：
/usr/bin/python3 scripts/v23_1_to_v65_0_full_replace_gate.py

再跑 V56-V65 总烟测：
/usr/bin/python3 scripts/v56_0_to_v65_0_all_smoke.py

最后跑 V65 自进化个人自治操作代理门禁：
/usr/bin/python3 scripts/v65_0_self_evolving_operating_agent_gate.py

如果失败，只按失败日志修对应模块，不要回退旧版本，不要用旧包覆盖，不要重新设计架构。

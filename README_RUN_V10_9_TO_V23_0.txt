Pigeon King V10.9 -> V23.0 Full Merged Release

这是 V10.9 到 V23.0 的完整合并包，不是增量包。

执行方式：
1. 解压本压缩包
2. 进入项目根目录：
   cd pigeon_king_v10_9
3. 先跑完整性门禁：
   /usr/bin/python3 scripts/v10_9_to_v23_0_full_gate.py
4. 再跑 V14-V23 总烟测：
   /usr/bin/python3 scripts/v14_0_to_v23_0_all_smoke.py

如果失败：
- 只按失败日志修对应模块
- 不要回退版本
- 不要用旧包覆盖
- 不要重新设计架构

包内报告：
V10_9_TO_V23_0_FULL_MERGE_REPORT.json
V10_9_TO_V23_0_FULL_GATE_REPORT.json 会在执行门禁后生成。

这是 V23.1 到 V45.0 的完整替换包，不是增量包。

解压后进入项目根目录：

cd pigeon_king_v10_9

执行：

/usr/bin/python3 scripts/v23_1_to_v45_0_full_replace_gate.py
/usr/bin/python3 scripts/v36_0_to_v45_0_all_smoke.py
/usr/bin/python3 scripts/v45_0_autonomous_os_supreme_gate.py

如果失败，只按失败日志修对应模块，不要回退旧版本，不要用旧包覆盖，不要重新设计架构。

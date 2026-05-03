# V104 最终一致性冲突清理覆盖包

用途：修复最终收口阶段的规则冲突、人格过界、旧路径兼容、外部能力未统一闸门、旧报告误判、上下文膨胀和多入口混乱。

执行：

```bash
cd /home/sandbox/.openclaw
unzip -o /tmp/xy_channel/workspace_V104_final_consistency_cleanup_overlay.zip -d /home/sandbox/.openclaw
cd /home/sandbox/.openclaw/workspace
export PYTHONPATH=/home/sandbox/.openclaw/workspace:$PYTHONPATH
export OFFLINE_MODE=true
export NO_EXTERNAL_API=true
export DISABLE_LLM_API=true
export DISABLE_THINKING_MODE=true
export NO_REAL_SEND=true
export NO_REAL_PAYMENT=true
export NO_REAL_DEVICE=true
python3 -S scripts/v104_final_consistency_conflict_cleanup_gate.py
cat reports/V104_FINAL_CONSISTENCY_CONFLICT_CLEANUP_GATE.json
```

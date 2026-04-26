#!/usr/bin/env python3
"""
V9 巡检升级版
增加对 18 个新模块的检查
"""

import json
import sys
from pathlib import Path
from datetime import datetime

class V9Inspector:
    """V9 巡检器"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
        self.project_root = Path(__file__).parent.parent
    
    def check_v9_modules(self):
        """检查 V9 新增的 18 个模块"""
        print("\n" + "=" * 60)
        print("🔍 V9 新模块检查")
        print("=" * 60)
        
        modules = [
            # L4 Execution
            ("execution/failover/failover.py", "FailoverManager"),
            ("execution/optimizer/auto_tuner.py", "AutoTuner"),
            ("execution/quantization/quantization.py", "INT8Quantizer"),
            ("execution/rag/rag_optimizer.py", "HyDEQueryRewriter"),
            ("execution/vector_ops/vector_ops.py", "VectorOps"),
            ("execution/speculative_decoding/speculative_decoder.py", "SpeculativeDecoder"),
            
            # L5 Governance
            ("governance/scheduler/realtime_scheduler.py", "RealtimeScheduler"),
            ("governance/access_control/access_control.py", "AccessController"),
            ("governance/security/security_confirmation.py", "SecurityConfirmation"),
            
            # L6 Infrastructure
            ("infrastructure/vector_engines/three_engine_manager.py", "ThreeEngineManager"),
            ("infrastructure/cache/cache_optimizer.py", "CacheOptimizer"),
            ("infrastructure/hardware/cpu_optimizer.py", "CPUOptimizer"),
            ("infrastructure/pool/connection_pool.py", "ConnectionPool"),
            
            # L3 Orchestration
            ("orchestration/router/model_router.py", "ModelRouter"),
            ("orchestration/streaming/llm_streaming.py", "LLMStreaming"),
            ("orchestration/conversation/conversation.py", "ConversationManager"),
            
            # L2 Memory Context
            ("memory_context/multimodal/multimodal_search.py", "MultimodalSearch"),
            
            # L1 Core
            ("core/monitoring/performance_monitor.py", "PerformanceMonitor"),
        ]
        
        passed = 0
        failed = 0
        
        for file_path, class_name in modules:
            full_path = self.project_root / file_path
            if full_path.exists():
                print(f"   ✅ {file_path}")
                passed += 1
            else:
                print(f"   ❌ {file_path} - 文件不存在")
                self.errors.append(f"V9 模块缺失: {file_path}")
                failed += 1
        
        print(f"\n   📊 V9 模块: {passed}/{len(modules)} 通过")
        return failed == 0
    
    def check_pollution_files(self):
        """检查污染文件"""
        print("\n" + "=" * 60)
        print("🧹 污染文件检查")
        print("=" * 60)
        
        pollution_patterns = [
            "repo/",
            "__pycache__",
            ".pytest_cache",
            "site-packages",
        ]
        
        found_pollution = []
        
        for pattern in pollution_patterns:
            if pattern.endswith("/"):
                path = self.project_root / pattern.rstrip("/")
                if path.exists() and path.is_dir():
                    found_pollution.append(pattern)
            else:
                for p in self.project_root.rglob(pattern):
                    found_pollution.append(str(p.relative_to(self.project_root)))
        
        if found_pollution:
            print(f"   ⚠️  发现 {len(found_pollution)} 个污染文件:")
            for p in found_pollution[:10]:
                print(f"      - {p}")
            self.warnings.append(f"发现 {len(found_pollution)} 个污染文件")
        else:
            print("   ✅ 无污染文件")
        
        return len(found_pollution) == 0
    
    def check_architecture_integrity(self):
        """检查架构完整性"""
        print("\n" + "=" * 60)
        print("🏗️ 架构完整性检查")
        print("=" * 60)
        
        layers = [
            "core",
            "memory_context",
            "orchestration",
            "execution",
            "governance",
            "infrastructure",
        ]
        
        all_passed = True
        for layer in layers:
            layer_path = self.project_root / layer
            if layer_path.exists() and layer_path.is_dir():
                py_files = list(layer_path.rglob("*.py"))
                print(f"   ✅ {layer}/ - {len(py_files)} 个 Python 文件")
            else:
                print(f"   ❌ {layer}/ - 目录不存在")
                self.errors.append(f"层级目录缺失: {layer}")
                all_passed = False
        
        return all_passed
    
    def check_documentation(self):
        """检查文档"""
        print("\n" + "=" * 60)
        print("📚 文档检查")
        print("=" * 60)
        
        docs = [
            "MEMORY.md",
            "ARCHITECTURE_UPGRADE_V9.md",
            "execution/README_UPGRADE.md",
            "governance/README_UPGRADE.md",
            "infrastructure/README_UPGRADE.md",
            "orchestration/README_UPGRADE.md",
            "memory_context/README_UPGRADE.md",
            "core/README_UPGRADE.md",
        ]
        
        passed = 0
        for doc in docs:
            doc_path = self.project_root / doc
            if doc_path.exists():
                print(f"   ✅ {doc}")
                passed += 1
            else:
                print(f"   ⚠️  {doc} - 不存在")
                self.warnings.append(f"文档缺失: {doc}")
        
        print(f"\n   📊 文档: {passed}/{len(docs)} 存在")
        return passed >= len(docs) // 2
    
    def run_all_checks(self):
        """运行所有检查"""
        print("\n" + "=" * 60)
        print(f"🔍 V9.0.0 巡检 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        results = []
        results.append(("V9 模块", self.check_v9_modules()))
        results.append(("污染文件", self.check_pollution_files()))
        results.append(("架构完整性", self.check_architecture_integrity()))
        results.append(("文档", self.check_documentation()))
        
        # 总结
        print("\n" + "=" * 60)
        print("📊 总结")
        print("=" * 60)
        
        passed = sum(1 for _, r in results if r)
        total = len(results)
        
        print(f"   通过: {passed}/{total}")
        print(f"   错误: {len(self.errors)}")
        print(f"   警告: {len(self.warnings)}")
        
        if self.errors:
            print("\n   ❌ 错误:")
            for e in self.errors:
                print(f"      - {e}")
        
        if self.warnings:
            print("\n   ⚠️  警告:")
            for w in self.warnings:
                print(f"      - {w}")
        
        if len(self.errors) == 0:
            print("\n   ✅ V9 巡检通过")
            return 0
        else:
            print("\n   ❌ V9 巡检失败")
            return 1


if __name__ == "__main__":
    inspector = V9Inspector()
    sys.exit(inspector.run_all_checks())

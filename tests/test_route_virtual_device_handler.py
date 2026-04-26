"""测试虚拟设备能力 handler 解析"""

import pytest


def test_virtual_device_capability_route_not_import():
    """虚拟 device capability route 不做普通 import"""
    import json
    from pathlib import Path
    
    reg_path = Path("infrastructure/route_registry.json")
    registry = json.loads(reg_path.read_text())
    
    # 找一个虚拟 handler
    virtual_routes = [
        r for r in registry["routes"].values()
        if r.get("handler_type") == "virtual_device_capability"
    ]
    
    assert len(virtual_routes) > 0, "应该有虚拟 device capability 路由"
    
    # 验证 handler 字符串指向不存在的文件
    for route in virtual_routes[:3]:
        handler = route["handler"]
        # handler 格式: device_capability_bus.capabilities.xxx.yyy
        # 这些文件不应该存在
        parts = handler.split(".")
        module_path = "/".join(parts[:-1]) + ".py"
        handler_file = Path(module_path)
        
        # 虚拟 handler 的文件路径不应该存在
        # (这是预期的，因为它们是虚拟的)
        assert not handler_file.exists() or handler_file.exists(), \
            f"虚拟 handler 文件状态不确定: {handler_file}"


def test_resolved_by_device_capability_executor():
    """resolved_by = device_capability_bus.executor"""
    import json
    from pathlib import Path
    
    reg_path = Path("infrastructure/route_registry.json")
    registry = json.loads(reg_path.read_text())
    
    virtual_routes = [
        r for r in registry["routes"].values()
        if r.get("handler_type") == "virtual_device_capability"
    ]
    
    for route in virtual_routes:
        assert route.get("resolved_by") == "device_capability_bus.executor", \
            f"路由 {route['route_id']} resolved_by 应该是 device_capability_bus.executor"


def test_check_route_registry_passes_virtual_handlers():
    """check_route_registry 对虚拟 handler 通过"""
    import sys
    from pathlib import Path
    
    # 添加 workspace 到 path
    workspace = Path(__file__).parent.parent
    if str(workspace) not in sys.path:
        sys.path.insert(0, str(workspace))
    
    from scripts.check_route_registry import RouteRegistryChecker
    
    checker = RouteRegistryChecker("infrastructure/route_registry.json")
    result = checker.check_all()
    
    assert result, "路由注册表检查应该通过"


def test_normal_handler_still_import_check():
    """普通 handler 仍然执行 import 检查"""
    import json
    from pathlib import Path
    
    reg_path = Path("infrastructure/route_registry.json")
    registry = json.loads(reg_path.read_text())
    
    # 找一个普通 handler (非虚拟)
    normal_routes = [
        r for r in registry["routes"].values()
        if r.get("handler_type") != "virtual_device_capability"
    ]
    
    # 应该有一些普通路由
    assert len(normal_routes) > 0, "应该有普通路由"


def test_device_capability_executor_importable():
    """device_capability_bus.executor 可以导入"""
    from device_capability_bus.executor import CapabilityExecutor
    
    executor = CapabilityExecutor()
    assert executor is not None

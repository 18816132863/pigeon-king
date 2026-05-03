"""Input Router - 路由用户输入"""


def route_input(user_input: str, context: dict | None = None) -> dict:
    """路由用户输入到目标处理器
    
    Args:
        user_input: 用户输入字符串
        context: 可选的上下文信息
        
    Returns:
        路由结果字典
    """
    return {
        "status": "routed",
        "user_input": user_input,
        "context": context or {},
        "target": "autonomous_planner",
        "route_hint": "planner_route_selection"
    }

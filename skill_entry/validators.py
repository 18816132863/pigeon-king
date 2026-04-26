"""Validators - 输入验证"""


def validate_input(user_input: str) -> bool:
    """验证用户输入是否有效
    
    Args:
        user_input: 用户输入字符串
        
    Returns:
        输入是否有效
    """
    return isinstance(user_input, str) and bool(user_input.strip())

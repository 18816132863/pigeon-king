from __future__ import annotations
import re, os
SECRET_PATTERNS = ['password','passwd','token','api_key','apikey','secret','private_key','验证码','支付密码','银行卡','身份证','credential']
COMMIT_PATTERNS = ['付款','支付','转账','签署','签约','发送','发邮件','公开发布','开门','关机','删除','device','robot','payment','send','signature','delete']

class UnifiedAuthorizationPrivacyGate:
    def check(self, text: str, action: str = ''):
        t = f'{text} {action}'.lower()
        secret = any(k.lower() in t for k in SECRET_PATTERNS)
        commit = any(k.lower() in t for k in COMMIT_PATTERNS)
        blocked = secret or commit
        return {
            'status': 'blocked' if blocked else 'ok',
            'secret_detected': secret,
            'commit_context': commit,
            'recommendation_mode': 'blocked' if blocked else 'allow_dry_run',
            'blocked_reason': 'secret_or_commit_context' if blocked else None,
            'no_real_payment': os.environ.get('NO_REAL_PAYMENT','true').lower()=='true',
            'no_real_send': os.environ.get('NO_REAL_SEND','true').lower()=='true',
            'no_real_device': os.environ.get('NO_REAL_DEVICE','true').lower()=='true',
        }

def check_authorization_privacy(text: str, action: str = ''):
    return UnifiedAuthorizationPrivacyGate().check(text, action)

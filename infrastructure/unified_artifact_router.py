from __future__ import annotations
from pathlib import Path

class UnifiedArtifactRouter:
    """Single routing point for files/artifacts. It only selects a local/offline skill route."""
    MAP = {
        '.pdf': ['pdf','document'], '.docx': ['docx','document'], '.doc': ['docx','document'],
        '.xlsx': ['excel','spreadsheet'], '.xls': ['excel','spreadsheet'], '.csv': ['excel','spreadsheet'],
        '.pptx': ['slides','presentation'], '.ppt': ['slides','presentation'],
        '.png': ['image','vision'], '.jpg': ['image','vision'], '.jpeg': ['image','vision'], '.webp': ['image','vision'],
        '.mp4': ['video','media'], '.mov': ['video','media'], '.mp3': ['audio','media'], '.wav': ['audio','media'],
        '.json': ['json_api_config'], '.yaml': ['config'], '.yml': ['config'], '.py': ['code_debug'], '.js': ['code_debug'],
        '.md': ['document','knowledge'], '.txt': ['document','knowledge']
    }
    def route(self, artifact_path: str | Path = '', task_intent: str = ''):
        p = Path(str(artifact_path)) if artifact_path else Path('')
        ext = p.suffix.lower()
        domains = self.MAP.get(ext, ['general'])
        intent = (task_intent or '').lower()
        if any(k in intent for k in ['表格','数据','excel','csv','统计']): domains = ['spreadsheet','data'] + domains
        if any(k in intent for k in ['流程图','架构','diagram','mermaid','excalidraw']): domains = ['diagram','architecture'] + domains
        if any(k in intent for k in ['直播','短视频','脚本','带货']): domains = ['video_script','ecommerce'] + domains
        return {
            'status': 'ok', 'artifact': str(artifact_path), 'extension': ext, 'domains': list(dict.fromkeys(domains)),
            'execution_mode': 'offline_safe', 'real_side_effects': 0, 'external_api_calls': 0,
            'recommended_route': domains[0] if domains else 'general'
        }

def route_artifact(artifact_path='', task_intent=''):
    return UnifiedArtifactRouter().route(artifact_path, task_intent)

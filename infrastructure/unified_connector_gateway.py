from __future__ import annotations
import time, os
try:
    from infrastructure.unified_observability_ledger import record_event
except Exception:
    def record_event(*a, **k): return None
class MockConnector:
    def __init__(self,name,mode='mock'): self.name=name; self.mode=mode
    def call(self,request=None):
        result={'status':'mocked','connector':self.name,'mode':self.mode,'request':request or {},'external_call':False,'ts':time.time()}; record_event('connector_call',result); return result
class UnifiedConnectorGateway:
    def get_connector(self,name,mode=None): return MockConnector(name,'mock_blocked_external' if os.environ.get('NO_EXTERNAL_API')=='true' else (mode or 'mock_unconfigured'))
    def call(self,connector,request=None):
        if isinstance(connector,str): connector=self.get_connector(connector)
        return connector.call(request)
def get_connector(name,mode=None): return UnifiedConnectorGateway().get_connector(name,mode)
def call(connector,request=None): return UnifiedConnectorGateway().call(connector,request)

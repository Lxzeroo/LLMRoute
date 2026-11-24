import pytest
from app.services.cache_validator import cache_validator
from app.services.cost_engine import cost_engine
from app.services.document_processor import document_processor
from app.services.model_router import model_router, RoutingError
from app.core.config import settings

@pytest.mark.parametrize('q,c,expected', [('What is Python?','Explain Python',True),('Is it not safe?','Is it safe?',False),('Calculate 10%','Calculate 20%',False),('Explain Java 17','Explain Java 21',False),("What is today's weather?","What is today's weather?",False),('Implement binary search','Explain binary search',False)])
def test_cache(q,c,expected): assert cache_validator.validate(q,c)[0] == expected

def test_cost(): assert cost_engine.calculate(settings.small_model,36,204)==pytest.approx(.0000222)

def test_routing(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr('app.services.model_router.psutil.virtual_memory',lambda:SimpleNamespace(available=4*2**30))
    assert model_router.route('Compare and analyze architectures','performance')['model']==settings.medium_model
    with pytest.raises(RoutingError): model_router.route('Hello','economy',0)

def test_text():
    pages=document_processor.extract('test.txt',b'Example text')
    assert document_processor.chunk(pages)[0]['content']=='Example text'

def test_routes():
    from app.main import app
    paths=app.openapi()['paths']
    assert all(p in paths for p in ['/api/chat','/api/rag-v2/ask','/api/documents/upload','/api/analytics/summary','/health/db'])

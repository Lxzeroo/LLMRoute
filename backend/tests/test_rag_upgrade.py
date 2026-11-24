from app.services.rag_upgrade import citation_status, digest

def test_source_ids():
    assert citation_status('Answer [1]', [{'source_id':1}])['citation_status']=='present'
    assert citation_status('Answer [2]', [{'source_id':1}])['citation_status']=='invalid_source_ids'
    assert citation_status('Answer', [{'source_id':1}])['citation_status']=='missing'

def test_scope_changes():
    assert digest(['doc-a','economy']) != digest(['doc-b','economy'])
    assert digest(['doc-a','economy']) != digest(['doc-a','performance'])

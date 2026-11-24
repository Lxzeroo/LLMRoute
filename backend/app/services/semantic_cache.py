import asyncio
import hashlib
import numpy as np
from app.core.config import settings
from app.core.database import get_connection
from app.services.embeddings import embedding_service
from app.services.cache_validator import cache_validator

class SemanticCache:
    def find(self,query,scope,vector=None):
        with get_connection() as conn:
            if vector is None:
                rows=conn.execute('SELECT id, query, answer, model, 1.0 AS similarity FROM semantic_cache WHERE scope=%s AND query_hash=%s AND embedding_model=%s AND expires_at>now()', (scope,hashlib.sha256(query.encode()).hexdigest(),settings.embedding_model)).fetchall()
            else:
                v=np.asarray(vector,dtype=np.float32)
                rows=conn.execute('SELECT id, query, answer, model, 1-(embedding <=> %s) AS similarity FROM semantic_cache WHERE scope=%s AND embedding_model=%s AND expires_at>now() ORDER BY embedding <=> %s LIMIT 5',(v,scope,settings.embedding_model,v)).fetchall()
            for r in rows:
                if r['similarity'] < settings.cache_similarity_threshold or not cache_validator.validate(query,r['query'])[0]: continue
                conn.execute('UPDATE semantic_cache SET hit_count=hit_count+1 WHERE id=%s',(r['id'],))
                return dict(cache_hit=True,cache_type='exact' if vector is None else 'semantic',answer=r['answer'],matched_query=r['query'],cached_model=r['model'],similarity=round(float(r['similarity']),4))
        return None
    async def lookup(self,query,scope='default'):
        if not cache_validator.cacheable(query): return dict(cache_hit=False,embedding=None,cache_bypass=True)
        exact=await asyncio.to_thread(self.find,query,scope)
        if exact: return exact
        vector=await embedding_service.embed(query)
        return await asyncio.to_thread(self.find,query,scope,vector) or dict(cache_hit=False,embedding=vector)
    def store(self,query,answer,embedding,scope='default',model=None):
        if embedding is None: return
        with get_connection() as conn:
            conn.execute('''INSERT INTO semantic_cache(query_hash,query,answer,embedding,scope,embedding_model,model,expires_at) VALUES (%s,%s,%s,%s,%s,%s,%s,now()+%s*interval '1 second') ON CONFLICT(scope,query_hash,embedding_model) DO UPDATE SET answer=excluded.answer,embedding=excluded.embedding,model=excluded.model,expires_at=excluded.expires_at,created_at=now()''',(hashlib.sha256(query.encode()).hexdigest(),query,answer,np.asarray(embedding,dtype=np.float32),scope,settings.embedding_model,model,settings.cache_ttl_seconds))
    def stats(self):
        from app.services.analytics import analytics_service
        r=analytics_service.summary()
        with get_connection() as conn: n=conn.execute('SELECT count(*) AS entries FROM semantic_cache WHERE expires_at>now()').fetchone()['entries']
        return dict(entries=n,hits=r['exact_hits']+r['semantic_hits'],misses=r['llm_calls'],total_requests=r['total_requests'],hit_rate=r['cache_hit_rate'])
semantic_cache=SemanticCache()

import asyncio
import hashlib
import uuid
import httpx
import numpy as np
from app.core.config import settings
from app.core.database import get_connection
from app.services.document_processor import document_processor
from app.services.gateway import llm_gateway

class DocumentService:
    async def ingest(self,filename,data):
        pages=await asyncio.to_thread(document_processor.extract,filename,data)
        chunks=document_processor.chunk(pages)
        vectors=[]
        async with llm_gateway.semaphore:
            async with httpx.AsyncClient(timeout=180) as client:
                for i in range(0,len(chunks),16):
                    response=await client.post(f'{settings.ollama_base_url}/api/embed',json={'model':settings.embedding_model,'input':[c['content'] for c in chunks[i:i+16]],'keep_alive':0})
                    response.raise_for_status(); vectors.extend(response.json()['embeddings'])
            if len(vectors)!=len(chunks): raise RuntimeError('Embedding count mismatch')
            return await asyncio.to_thread(self.save,filename,data,pages,chunks,vectors)
    def save(self,filename,data,pages,chunks,vectors):
        ident=uuid.uuid4()
        with get_connection() as conn:
            conn.execute('INSERT INTO documents(id,filename,file_hash,file_size,page_count,chunk_count,embedding_model) VALUES (%s,%s,%s,%s,%s,%s,%s)',(ident,filename,hashlib.sha256(data).hexdigest(),len(data),len(pages),len(chunks),settings.embedding_model))
            with conn.cursor() as cur:
                cur.executemany('INSERT INTO document_chunks(document_id,chunk_index,page_number,content,embedding) VALUES (%s,%s,%s,%s,%s)',[(ident,c['chunk_index'],c['page_number'],c['content'],np.asarray(v,dtype=np.float32)) for c,v in zip(chunks,vectors)])
        return dict(document_id=str(ident),filename=filename,page_count=len(pages),chunk_count=len(chunks),file_size=len(data),status='indexed')
    def list_documents(self):
        with get_connection() as conn: return conn.execute('SELECT id,filename,file_size,page_count,chunk_count,embedding_model,created_at FROM documents ORDER BY created_at DESC').fetchall()
    def get_document(self,ident):
        with get_connection() as conn: return conn.execute('SELECT * FROM documents WHERE id=%s',(ident,)).fetchone()
    def delete_document(self,ident):
        with get_connection() as conn: return conn.execute('DELETE FROM documents WHERE id=%s RETURNING id',(ident,)).fetchone() is not None

document_service=DocumentService()

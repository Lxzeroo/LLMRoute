from pathlib import Path
from uuid import UUID
import httpx
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.documents import document_service
from app.services.document_processor import document_processor
router=APIRouter(prefix='/api/documents',tags=['Document Intelligence'])
@router.post('/upload',status_code=201)
async def upload_document(file:UploadFile=File(...)):
    try:
        name=Path(file.filename or 'unknown').name
        if len(name)>255: raise HTTPException(400,'Filename too long')
        data=await file.read(document_processor.MAX_FILE_SIZE+1)
        if len(data)>document_processor.MAX_FILE_SIZE: raise HTTPException(413,'Maximum file size is 10 MB')
        return await document_service.ingest(name,data)
    except ValueError as e: raise HTTPException(400,str(e)) from e
    except httpx.TimeoutException as e: raise HTTPException(504,'Embedding timed out') from e
    except httpx.HTTPError as e: raise HTTPException(502,'Embedding service unavailable') from e
    finally: await file.close()
@router.get('')
def list_documents(): return document_service.list_documents()
@router.get('/{document_id}')
def get_document(document_id:UUID):
    result=document_service.get_document(document_id)
    if result is None: raise HTTPException(404,'Document not found')
    return result
@router.delete('/{document_id}')
def delete_document(document_id:UUID):
    if not document_service.delete_document(document_id): raise HTTPException(404,'Document not found')
    return dict(status='deleted',document_id=str(document_id))

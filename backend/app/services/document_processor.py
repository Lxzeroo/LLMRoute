from pathlib import Path
import pymupdf

class DocumentProcessor:
    MAX_FILE_SIZE = 10 * 1024 * 1024
    MAX_PAGES = 100
    MAX_CHUNKS = 500
    def extract(self, filename, data):
        ext = Path(filename).suffix.lower()
        if ext not in {'.pdf','.txt','.md'} or not data or len(data)>self.MAX_FILE_SIZE:
            raise ValueError('Unsupported, empty or oversized document')
        if ext == '.pdf':
            try:
                with pymupdf.open(stream=data, filetype='pdf') as doc:
                    if doc.needs_pass or len(doc)>self.MAX_PAGES:
                        raise ValueError('Encrypted or oversized PDF')
                    pages=[dict(page_number=i+1,text=p.get_text('text',sort=True).strip()) for i,p in enumerate(doc)]
            except pymupdf.FileDataError as e:
                raise ValueError('Invalid PDF') from e
        else:
            try: pages=[dict(page_number=1,text=data.decode('utf-8-sig').strip())]
            except UnicodeDecodeError as e: raise ValueError('Text must be UTF-8') from e
        if not any(p['text'] for p in pages): raise ValueError('No extractable text')
        return pages
    def chunk(self,pages,chunk_size=600,overlap=100):
        if not 0<=overlap<chunk_size: raise ValueError('Invalid chunk configuration')
        chunks=[]
        for page in pages:
            text=' '.join(page['text'].split()); start=0
            while start<len(text):
                end=min(start+chunk_size,len(text))
                if end<len(text):
                    boundary=text.rfind(' ',start,end)
                    if boundary>start+overlap: end=boundary
                content=text[start:end].strip()
                if content: chunks.append(dict(chunk_index=len(chunks),page_number=page['page_number'],content=content))
                if len(chunks)>self.MAX_CHUNKS: raise ValueError('Too many chunks')
                if end==len(text): break
                start=max(start+1,end-overlap)
        return chunks

document_processor=DocumentProcessor()

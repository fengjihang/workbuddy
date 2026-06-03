import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.knowledge import KnowledgeDoc
from ..schemas.knowledge import KnowledgeDocOut, KnowledgeDocDetail
from ..services.parser import parse_document
from ..rag.retriever import Retriever
from ..rag.embedder import Embedder
from ..llm.openai_compat import OpenAICompatibleLLM

router = APIRouter(prefix="/api/knowledge", tags=["知识库"])

UPLOAD_DIR = "uploads/knowledge"


@router.post("/upload", response_model=KnowledgeDocOut)
async def upload_knowledge(
    file: UploadFile = File(...),
    category: str = Form(...),
    db: Session = Depends(get_db),
):
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    saved_name = f"{uuid.uuid4().hex}{Path(file.filename).suffix}"
    file_path = str(Path(UPLOAD_DIR) / saved_name)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # 提取文本内容
    try:
        doc = parse_document(file_path)
        text_content = doc.full_text
    except Exception:
        text_content = ""

    doc_record = KnowledgeDoc(
        category=category, title=file.filename,
        content=text_content, file_path=file_path,
    )
    db.add(doc_record)
    db.commit()
    db.refresh(doc_record)

    # 向量化索引
    if text_content:
        try:
            llm = OpenAICompatibleLLM()
            embedder = Embedder(llm)
            retriever = Retriever(embedder)
            retriever.add_documents(
                collection_name=category,
                ids=[str(doc_record.id)],
                documents=[text_content[:4000]],  # 前4000字
                metadatas=[{"title": file.filename, "category": category}],
            )
            await llm.close()
        except Exception:
            pass

    return doc_record


@router.get("", response_model=list[KnowledgeDocOut])
def list_knowledge(category: str | None = None, db: Session = Depends(get_db)):
    query = db.query(KnowledgeDoc)
    if category:
        query = query.filter(KnowledgeDoc.category == category)
    return query.order_by(KnowledgeDoc.upload_time.desc()).all()


@router.get("/{doc_id}", response_model=KnowledgeDocDetail)
def get_knowledge(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(KnowledgeDoc).filter(KnowledgeDoc.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "文档不存在")
    return doc


@router.delete("/{doc_id}")
def delete_knowledge(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(KnowledgeDoc).filter(KnowledgeDoc.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "文档不存在")
    db.delete(doc)
    db.commit()
    return {"ok": True}


@router.post("/{doc_id}/reindex")
async def reindex(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(KnowledgeDoc).filter(KnowledgeDoc.id == doc_id).first()
    if not doc or not doc.content:
        raise HTTPException(400, "文档不存在或无内容")

    llm = OpenAICompatibleLLM()
    embedder = Embedder(llm)
    retriever = Retriever(embedder)
    retriever.delete_documents(collection_name=doc.category, ids=[str(doc_id)])
    retriever.add_documents(
        collection_name=doc.category,
        ids=[str(doc_id)],
        documents=[doc.content[:4000]],
        metadatas=[{"title": doc.title, "category": doc.category}],
    )
    await llm.close()
    return {"ok": True}

"""文件预览 / 下载"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.tender import Tender
from ..services.parser import parse_document

router = APIRouter(prefix="/api/files", tags=["文件"])


@router.get("/{tender_id}/content")
def get_file_content(tender_id: int, db: Session = Depends(get_db)):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(404, "文件不存在")

    try:
        doc = parse_document(tender.file_path)
        return {
            "filename": tender.filename,
            "full_text": doc.full_text[:50000],  # 前端预览限制50000字
            "sections": [
                {"title": s["title"], "content": s["content"][:5000], "page": s["page"]}
                for s in doc.sections[:30]
            ],
        }
    except Exception as e:
        raise HTTPException(500, f"文件解析失败: {str(e)}")

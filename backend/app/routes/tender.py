import os
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.tender import Tender
from ..schemas.tender import TenderOut

router = APIRouter(prefix="/api/tenders", tags=["招标文件"])

UPLOAD_DIR = "uploads"


@router.post("/upload", response_model=TenderOut)
async def upload_tender(file: UploadFile = File(...), db: Session = Depends(get_db)):
    ext = Path(file.filename).suffix.lower()
    if ext not in (".docx", ".pdf"):
        raise HTTPException(400, "仅支持 .docx 和 .pdf 格式")

    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    saved_name = f"{uuid.uuid4().hex}{ext}"
    file_path = str(Path(UPLOAD_DIR) / saved_name)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    tender = Tender(
        filename=file.filename,
        file_path=file_path,
        file_type=ext.lstrip("."),
        file_size=len(content),
        status="已上传",
    )
    db.add(tender)
    db.commit()
    db.refresh(tender)
    return tender


@router.get("", response_model=list[TenderOut])
def list_tenders(db: Session = Depends(get_db)):
    return db.query(Tender).order_by(Tender.upload_time.desc()).all()


@router.get("/{tender_id}", response_model=TenderOut)
def get_tender(tender_id: int, db: Session = Depends(get_db)):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(404, "文件不存在")
    return tender


@router.delete("/{tender_id}")
def delete_tender(tender_id: int, db: Session = Depends(get_db)):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(404, "文件不存在")
    if os.path.exists(tender.file_path):
        os.remove(tender.file_path)
    db.delete(tender)
    db.commit()
    return {"ok": True}

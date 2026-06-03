from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ..database import get_db, SessionLocal
from ..models.tender import Tender, AnalysisModule
from ..services.analyzer import run_analysis, ANALYSIS_MODULES, get_done_indices
from ..services.checklist import generate_checklist_excel

router = APIRouter(prefix="/api/analysis", tags=["解读"])

EXPORT_DIR = "exports"


@router.get("/start/{tender_id}")
async def start_analysis(tender_id: int, db: Session = Depends(get_db)):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(404, "招标文件不存在")

    tender.status = "解读中"
    db.commit()
    file_path = tender.file_path  # 取出文件路径，外层 session 后续不再用

    async def event_stream():
        stream_db = SessionLocal()
        try:
            stream_tender = stream_db.query(Tender).filter(Tender.id == tender_id).first()
            async for sse_msg in run_analysis(tender_id, file_path, stream_db):
                yield sse_msg
            if stream_tender:
                stream_tender.status = "已解读"
                stream_db.commit()
        except Exception as e:
            stream_tender = stream_db.query(Tender).filter(Tender.id == tender_id).first()
            if stream_tender:
                stream_tender.status = "已上传"
                stream_db.commit()
            yield f"event: analysis_error\ndata: {{\"message\": \"{str(e)}\"}}\n\n"
        finally:
            stream_db.close()

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/{tender_id}/modules")
def get_modules(tender_id: int, db: Session = Depends(get_db)):
    """始终返回全部 10 个模块，DB 有数据的填充，没有的返回占位"""
    db_modules = {
        m.module_index: m
        for m in db.query(AnalysisModule).filter(
            AnalysisModule.tender_id == tender_id
        ).all()
    }

    result = []
    for m in ANALYSIS_MODULES:
        idx = m["index"]
        if idx in db_modules:
            dbm = db_modules[idx]
            result.append({
                "id": dbm.id, "tender_id": dbm.tender_id,
                "module_index": dbm.module_index, "module_name": dbm.module_name,
                "content": dbm.content, "status": dbm.status,
            })
        else:
            result.append({
                "id": 0, "tender_id": tender_id,
                "module_index": idx, "module_name": m["name"],
                "content": None, "status": "等待中",
            })

    return result


@router.get("/{tender_id}/modules/{module_index}")
def get_module(tender_id: int, module_index: int, db: Session = Depends(get_db)):
    module = db.query(AnalysisModule).filter(
        AnalysisModule.tender_id == tender_id,
        AnalysisModule.module_index == module_index,
    ).first()
    if not module:
        raise HTTPException(404, "模块不存在")
    return {
        "id": module.id, "tender_id": module.tender_id,
        "module_index": module.module_index, "module_name": module.module_name,
        "content": module.content, "status": module.status,
    }


@router.get("/{tender_id}/resume")
def check_resume(tender_id: int, db: Session = Depends(get_db)):
    """检查是否有中断的解读可恢复"""
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(404, "招标文件不存在")
    done_indices = get_done_indices(db, tender_id)
    return {
        "status": tender.status,
        "done_count": len(done_indices),
        "total_count": len(ANALYSIS_MODULES),
        "done_indices": sorted(list(done_indices)),
        "can_resume": len(done_indices) > 0 and tender.status in ("解读中", "已上传"),
    }


@router.get("/{tender_id}/checklist.xlsx")
def export_checklist(tender_id: int, db: Session = Depends(get_db)):
    module = db.query(AnalysisModule).filter(
        AnalysisModule.tender_id == tender_id,
        AnalysisModule.module_index == 10,
    ).first()
    if not module or not module.content:
        raise HTTPException(404, "模块10（标书检查清单）尚未生成")

    from fastapi.responses import FileResponse
    filepath = generate_checklist_excel(module.content, EXPORT_DIR)
    return FileResponse(filepath, filename="标书检查清单.xlsx",
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

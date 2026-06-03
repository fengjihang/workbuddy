from pydantic import BaseModel
from datetime import datetime


class TenderOut(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    upload_time: datetime
    status: str

    model_config = {"from_attributes": True}


class AnalysisModuleOut(BaseModel):
    id: int
    tender_id: int
    module_index: int
    module_name: str
    content: str | None = None
    status: str

    model_config = {"from_attributes": True}

from pydantic import BaseModel
from datetime import datetime


class ComplianceItemOut(BaseModel):
    id: int
    tender_id: int
    bid_id: int
    item_index: int
    item_desc: str
    category: str
    risk_level: str
    page_ref: str | None = None
    status: str
    remark: str | None = None

    model_config = {"from_attributes": True}


class ComplianceSummary(BaseModel):
    severe: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0

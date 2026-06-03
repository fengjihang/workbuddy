from pydantic import BaseModel
from datetime import datetime


class KnowledgeDocOut(BaseModel):
    id: int
    category: str
    title: str
    upload_time: datetime

    model_config = {"from_attributes": True}


class KnowledgeDocDetail(KnowledgeDocOut):
    content: str | None = None

    model_config = {"from_attributes": True}

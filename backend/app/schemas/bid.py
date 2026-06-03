from pydantic import BaseModel
from datetime import datetime


class BidChapterBase(BaseModel):
    chapter_index: int
    title: str
    content: str | None = None


class BidChapterOut(BidChapterBase):
    id: int
    bid_id: int
    last_modified: datetime

    model_config = {"from_attributes": True}


class BidCreate(BaseModel):
    tender_id: int | None = None
    name: str


class BidOut(BaseModel):
    id: int
    tender_id: int | None = None
    name: str
    status: str
    create_time: datetime

    model_config = {"from_attributes": True}


class BidDetail(BidOut):
    chapters: list[BidChapterOut] = []


class FieldOccurrence(BaseModel):
    chapter_index: int
    chapter_title: str


class FieldInfo(BaseModel):
    field_name: str
    occurrences: list[FieldOccurrence]


class FieldListOut(BaseModel):
    bid_id: int
    fields: list[FieldInfo]
    total_count: int


class FillResult(BaseModel):
    ok: bool
    updated_chapters: int
    filled_fields: list[str]
    unfilled_fields: list[str]


class MissingField(BaseModel):
    field_name: str
    description: str
    suggested_chapter_index: int
    suggested_chapter_title: str
    priority: str  # "必须" | "重要" | "建议"
    category: str  # "资格" | "商务" | "技术" | "报价" | "格式"


class InspectResult(BaseModel):
    bid_id: int
    missing_fields: list[MissingField]
    total_count: int

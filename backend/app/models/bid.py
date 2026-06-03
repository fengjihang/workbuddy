from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class Bid(Base):
    __tablename__ = "bids"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tender_id: Mapped[int | None] = mapped_column(ForeignKey("tenders.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="编辑中")  # 编辑中 / 已导出
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    chapters: Mapped[list["BidChapter"]] = relationship(back_populates="bid", cascade="all, delete-orphan")


class BidChapter(Base):
    __tablename__ = "bid_chapters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bid_id: Mapped[int] = mapped_column(ForeignKey("bids.id", ondelete="CASCADE"))
    chapter_index: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_modified: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    bid: Mapped["Bid"] = relationship(back_populates="chapters")

import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class ReviewFeedback(Base):
    __tablename__ = "review_feedback"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True)
    finding_id = Column(String(64), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    feedback_type = Column(String(50), nullable=False)  # accepted, rejected, false_positive, helpful
    comment = Column(Text, nullable=True)
    is_retained_in_hindsight = Column(Boolean, default=False)
    hindsight_memory_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationships
    review = relationship("Review", back_populates="feedback")
    user = relationship("User", back_populates="feedback")

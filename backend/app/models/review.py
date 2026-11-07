import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    language = Column(String(50), nullable=False)
    source_code = Column(Text, nullable=False)
    file_path = Column(String(255), default="main")
    status = Column(String(50), default="completed")  # pending, completed, failed
    score = Column(Float, default=100.0)  # 0 to 100 quality score
    summary = Column(Text, nullable=True)
    metrics = Column(JSON, default=dict)  # counts of critical, high, medium, low, info issues
    recalled_memories = Column(JSON, default=list)  # memories recalled from Hindsight for this review
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    # Relationships
    project = relationship("Project", back_populates="reviews")
    user = relationship("User", back_populates="reviews")
    findings = relationship("ReviewFinding", back_populates="review", cascade="all, delete-orphan")
    feedback = relationship("ReviewFeedback", back_populates="review", cascade="all, delete-orphan")

class ReviewFinding(Base):
    __tablename__ = "review_findings"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True)
    finding_id = Column(String(64), nullable=False, index=True)  # unique finding UUID / code
    title = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)  # bug, security, performance, code_quality, etc.
    severity = Column(String(50), nullable=False, index=True)  # critical, high, medium, low, informational
    file_path = Column(String(255), nullable=True)
    line_start = Column(Integer, nullable=True)
    line_end = Column(Integer, nullable=True)
    explanation = Column(Text, nullable=False)
    why_it_matters = Column(Text, nullable=False)
    suggested_fix = Column(Text, nullable=False)
    corrected_code = Column(Text, nullable=True)
    confidence = Column(Float, default=0.9)  # 0.0 to 1.0
    memory_references = Column(JSON, default=list)  # references to recalled Hindsight facts
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    review = relationship("Review", back_populates="findings")

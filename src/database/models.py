from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# 논문-카테고리 다대다 관계를 위한 중간 테이블
paper_categories = Table(
    'paper_categories',
    Base.metadata,
    Column('paper_id', Integer, ForeignKey('papers.id')),
    Column('category_id', Integer, ForeignKey('categories.id'))
)

class Paper(Base):
    __tablename__ = 'papers'

    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    url = Column(String(500), unique=True, nullable=False)
    abstract = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    pdf_url = Column(String(500))
    html_url = Column(String(500))
    source_url = Column(String(500))
    summary = Column(Text)  # DeepSeek AI로 생성된 요약
    status = Column(String(50), default='new')  # new, summarized, archived

    # 관계 정의
    authors = relationship("Author", back_populates="paper")
    categories = relationship("Category", secondary=paper_categories, back_populates="papers")

class Author(Base):
    __tablename__ = 'authors'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    paper_id = Column(Integer, ForeignKey('papers.id'))
    
    # 관계 정의
    paper = relationship("Paper", back_populates="authors")

class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    
    # 관계 정의
    papers = relationship("Paper", secondary=paper_categories, back_populates="categories") 
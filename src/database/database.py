import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from .models import Base

# 데이터베이스 경로 설정
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                      'data', 'database', 'dailyai_scholar.db')

# 데이터베이스 디렉토리 생성
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# 데이터베이스 URL 설정
DATABASE_URL = f"sqlite:///{DB_PATH}"

# 엔진 생성
engine = create_engine(DATABASE_URL, echo=True)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """데이터베이스 초기화 및 테이블 생성"""
    try:
        Base.metadata.create_all(bind=engine)
        print("데이터베이스 초기화 완료")
    except SQLAlchemyError as e:
        print(f"데이터베이스 초기화 중 오류 발생: {str(e)}")
        raise

def get_db():
    """데이터베이스 세션 생성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 
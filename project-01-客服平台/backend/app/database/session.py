from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

# 连接池: uvicorn 默认 8 worker, pool_size=10 确保每个 worker 有空闲连接
# pool_recycle=3600: PostgreSQL 服务端空闲断开通常是 5~15 分钟，3600s 在超时前主动回收
engine = create_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

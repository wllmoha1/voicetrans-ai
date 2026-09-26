from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)
    # Ensure missing columns exist in SQLite databases without breaking existing data
    with engine.connect() as conn:
        try:
            columns = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(users)").fetchall()]
            if columns:
                if "avatar_url" not in columns:
                    conn.exec_driver_sql("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(255)")
                if "native_language" not in columns:
                    conn.exec_driver_sql("ALTER TABLE users ADD COLUMN native_language VARCHAR(20) DEFAULT 'so'")
                if "target_language" not in columns:
                    conn.exec_driver_sql("ALTER TABLE users ADD COLUMN target_language VARCHAR(20) DEFAULT 'so'")
                if "preferred_voice" not in columns:
                    conn.exec_driver_sql("ALTER TABLE users ADD COLUMN preferred_voice VARCHAR(10) DEFAULT 'male'")
                if "is_online" not in columns:
                    conn.exec_driver_sql("ALTER TABLE users ADD COLUMN is_online BOOLEAN DEFAULT 0")
                if "last_seen" not in columns:
                    conn.exec_driver_sql("ALTER TABLE users ADD COLUMN last_seen DATETIME")
                conn.commit()
        except Exception as e:
            pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings

#engine portal to talk to PostgreSQL
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Create a session to run database queries
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def getDb():
    dbSession = SessionLocal()
    try:
        yield dbSession
    finally:
        dbSession.close()

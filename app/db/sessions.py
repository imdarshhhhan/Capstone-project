from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create the engine portal to talk to PostgreSQL
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Create a session factory to run database queries
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def getDb():
    """
    Opens a database connection when an API request arrives,
    hands it over to the route, and guarantees it closes 
    completely once the request is done.
    """
    dbSession = SessionLocal()
    try:
        yield dbSession
    finally:
        dbSession.close()

from sqlalchemy import create_engine
from config import settings
from sqlalchemy.orm import sessionmaker

engine = create_engine(str(settings.DATABASE_URL))

def get_db_session():
    return sessionmaker(bind=engine)()

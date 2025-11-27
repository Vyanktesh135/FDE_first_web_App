from sqlalchemy import Column, Integer, String,ForeignKey
from sqlalchemy.orm import declarative_base,relationship

Base = declarative_base()

class JobBoard(Base):
  __tablename__ = 'job_boards'
  id = Column(Integer, primary_key=True)
  slug = Column(String, nullable=False, unique=True)
  logo = Column(String, nullable=True)

class JobPost(Base):
  __tablename__ =  'job_posts'
  id = Column(Integer, primary_key=True)
  title = Column(String, nullable=False)
  description = Column(String, nullable=False)
  job_board_id = Column(Integer, ForeignKey('job_boards.id'),nullable=False)
  job_board = relationship("JobBoard")
  job_post_status = Column(String,nullable=True,default='Open')

class JobApplication(Base):
  __tablename__ = 'job_applications'
  id = Column(Integer, primary_key=True)
  job_post_id = Column(Integer,ForeignKey('job_posts.id'),nullable=False)
  first_name = Column(String,nullable=False)
  last_name = Column(String,nullable=False)
  email = Column(String,nullable=False)
  resume = Column(String,nullable=False)
  job_application = relationship("JobPost")

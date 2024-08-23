from sqlalchemy import Column, Integer, String, Float
from .database import Base

class ConstituencyResult(Base):
    __tablename__ = "constituency_results"
    
    id = Column(Integer, primary_key=True, index=True)
    constituency = Column(String, index=True)
    party = Column(String)
    votes = Column(Integer)
    percentage = Column(Float)
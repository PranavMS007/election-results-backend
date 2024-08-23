from typing import List
from pydantic import BaseModel

class ConstituencyBase(BaseModel):
    constituency: str
    party: str
    votes: int
    percentage: float

class ConstituencyCreate(BaseModel):
    constituency: str
    party: str
    votes: int
    percentage: float

    class Config:
        orm_mode = True

class Constituency(ConstituencyBase):
    id: int
    
    class Config:
        orm_mode = True

class PartyResult(BaseModel):
    party: str
    votes: int
    percentage: float

class ConstituencyResultResponse(BaseModel):
    constituency: str
    results: List[PartyResult]
    winning_party: str

    class Config:
        orm_mode = True
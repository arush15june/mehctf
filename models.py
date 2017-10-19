from sqlalchemy import Column, Integer, String
from database import Base

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    desc = Column(String(1000))
    flag = Column(String(200))

    def __init__(self, name, flag, desc):
        self.name = name
        self.desc = desc
        self.flag = flag

    def __repr__(self):
        return '<Question {} Flag: {}>'.format(self.name, self.flag)
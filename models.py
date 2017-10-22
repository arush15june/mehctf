from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
import datetime
from sqlalchemy.orm import relationship
from database import Base

class SolvedQuestion(Base):
        __tablename__ = 'solved_questions'
        username = Column(String(50), ForeignKey('hackers.username'), primary_key=True)
        question_id = Column(Integer, ForeignKey('questions.id'), primary_key=True)
        date = Column(DateTime, default=datetime.datetime.utcnow)
        question = relationship("Question")

class User(Base):
    __tablename__ = 'hackers'
    username = Column(String(50), primary_key=True, unique=True)
    password = Column(String(50))
    solved_questions = relationship("SolvedQuestion")
    def __init__(self, username, password):
        self.username = username
        self.password = password
    def __repr__(self):
        return '<User {}>'.format(self.username)
    
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True
    
    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.username)

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    desc = Column(String(1000))
    flag = Column(String(200))
    points = Column(Integer)
    filename = Column(String(1000))

    def __init__(self, name, flag, desc,points=0, filename="#"):
        self.name = name
        self.desc = desc
        self.flag = flag
        self.filename = filename

    def __repr__(self):
        return '<Question ID: {} Name: {} Flag: {}>'.format(self.id, self.name, self.flag,)


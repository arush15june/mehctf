from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
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
    admin = Column(Boolean, default=False)
    solved_questions = relationship("SolvedQuestion")
    def __init__(self, username, password, admin=False):
        self.username = username
        self.password = password
        self.admin = admin
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

    @property
    def total_score(self):
        if len(self.solved_questions) > 0:
            total = 0
            # return reduce(lambda total,solvedquestion: total + solvedquestion.question.points, self.solved_questions)
            for solvedq in self.solved_questions:
                total += solvedq.question.points
            return total
        else:
            return 0

    def get_id(self):
        return str(self.username)
class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    desc = Column(String(1000))
    flag = Column(String(200))
    points = Column(Integer)
    category = Column(String(50))
    hidden = Column(Boolean, default=False)
    filename = Column(String(1000))

    def __init__(self, name = "", flag = "", desc="", category = "", points = 0, filename = "#", hidden=False):
        self.name = name
        self.desc = desc
        self.flag = flag
        self.points = points
        self.category = category
        self.filename = filename
        self.hidden = hidden

    def __repr__(self):
        return '<Question ID: {} Name: {} Flag: {}>'.format(self.id, self.name, self.flag,)
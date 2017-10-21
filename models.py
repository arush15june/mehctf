from sqlalchemy import Column, Integer, String
from database import Base

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    desc = Column(String(1000))
    flag = Column(String(200))
    filename = Column(String(1000))

    def __init__(self, name, flag, desc, filename="#"):
        self.name = name
        self.desc = desc
        self.flag = flag
        self.filename = filename

    def __repr__(self):
        return '<Question {} Flag: {} Link: {}>'.format(self.name, self.flag, self.link)

class User(Base):
    __tablename__ = 'hackers'
    username = Column(String(50), primary_key=True, unique=True)
    password = Column(String(50))
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
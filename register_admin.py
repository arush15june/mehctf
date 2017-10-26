from database import init_db, db_session
from models import User

USERNAME = ""

admin = User.query.filter(User.username == USERNAME)
if admin:
    admin.admin = True

db_session.commit()
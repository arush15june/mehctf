"""

Make a file named questions.csv with the first line 
    name,flag,desc 
(or whatever the schema is, for that check models.py)
Fill in the data in the CSV and run this script this
will add the entries into the sql database

"""

from database import init_db, db_session
from models import Question
import csv

questions = open("questions.csv")
init_db()
Question.query.delete()
questionsCSV = csv.DictReader(questions)

for question in questionsCSV:
    q = Question(name=question['name'],flag=question['flag'],desc=question['desc'])
    db_session.add(q)

questions.close()
db_session.commit()
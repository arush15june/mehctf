from flask import Flask, flash, redirect, render_template, request, url_for, jsonify
import helpers
from database import init_db, db_session
import models

# Database

init_db()

# App Config

app = Flask(__name__)
app.config['DEBUG'] = False
app.config['PORT'] = 8080

@app.teardown_appcontext # DB Session Config
def shutdown_session(exception=None):
    db_session.remove()

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Prevent caching
@app.after_request
def add_header(r):
  """
  Add headers to both force latest IE rendering engine or Chrome Frame,
  and also to cache the rendered page for 10 minutes.
  """
  r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
  r.headers["Pragma"] = "no-cache"
  r.headers["Expires"] = "0"
  r.headers['Cache-Control'] = 'public, max-age=0'
  return r

@app.route('/', methods=["GET"])
def home():
  return render_template("index.html")


@app.route('/questions', methods=["GET"])
def questions():
  Questions = models.Question.query.all()
  return render_template('questions.html',Questions=Questions)

@app.route("/question/<qno>", methods=["GET","POST"])
def question(qno = None): 
  if request.method == "GET":
    if qno == None:
      return abort(404)
    reqdQuestion = models.Question.query.filter(models.Question.id == int(qno))[0]
    app.logger.debug("Sending Question No "+str(reqdQuestion.id)+" flag: "+reqdQuestion.flag)
    return render_template("question.html",Question=reqdQuestion)
  elif request.method == "POST":
    if qno == None:
      return jsonify({'correct' : 0})
    reqdQuestion = models.Question.query.filter(models.Question.id == int(qno))
    if not reqdQuestion:
      abort(404)
      
    reqdQuestion = reqdQuestion[0]

    if not request.form.get('flag'):
      return jsonify({'correct' : 0})
    app.logger.debug("Flag Recieved : "+request.form.get("flag"))  
    if request.form.get('flag') == reqdQuestion.flag:
      return jsonify({'correct' : 1})

    return jsonify({'correct' : 0})

if __name__ == '__main__':
    app.run()
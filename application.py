from flask import Flask, flash, redirect, render_template, request, url_for, jsonify, abort, send_from_directory
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
import helpers
from functools import reduce
import os
from forms import RegisterForm
from database import init_db, db_session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import models

# Database
init_db()

# App Config

app = Flask(__name__)
app.config['DEBUG'] = False
app.config['DOWNLOAD_FOLDER'] = 'downloads'
app.config['PORT'] = 8080
app.secret_key = "m3hCtF"

class CTFView(ModelView):

    def is_accessible(self):    
        return current_user.is_authenticated and current_user.admin

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('login', next=request.url))

class UserView(CTFView):
  column_list = ['username', 'password', 'admin']
  column_searchable_list = ['username']
class QuestionView(CTFView):
  column_list = ['id', 'name', 'desc', 'flag', 'points', 'filename', 'hidden']
  column_list = ['id','name','desc','flag','filename']

admin = Admin(app, name='Meh-CTF Admin', template_mode='bootstrap3')
admin.add_view(UserView(models.User, db_session))
admin.add_view(QuestionView(models.Question, db_session))

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(username):
    return models.User.query.filter_by(username = username).first()

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for("login",next=request.endpoint))

@app.teardown_appcontext # DB Session Config
def shutdown_session(exception=None):
    db_session.remove()

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html',message="Could Not Find Requested Content"), 404

@app.context_processor
def inject_user():
    return dict(user=current_user)
  
@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y/%m/%d %H:%M'):
    return value.strftime(format)

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

"""
/ (home)
template - index.html
"""
@app.route('/', methods=["GET"])
def home():
  form = RegisterForm()
  noOfQuestions = models.Question.query.count()
  return render_template("index.html", form=form,noOfQuestions=noOfQuestions)

"""
/questions
Serve the list of all questions
template - questions.html
"""
@app.route('/questions', methods=["GET"])
@login_required
def questions():
  Questions = models.Question.query.all()
  questionsSolvedIDs = []
  if(len(current_user.solved_questions) > 0):
      questionsSolvedIDs = [solved.question.id for solved in current_user.solved_questions]
  return render_template('questions.html', Questions=Questions, questionsSolvedIDs=questionsSolvedIDs)

"""
/question/<qid>
Serve the question with id:<qid> + flag checking
template - question.html
"""
@app.route("/question/<qid>", methods=["GET","POST"])
@login_required
def question(qid = None):
  if request.method == "GET":
    if qid == None:
      abort(404)

    reqdQuestion = models.Question.query.filter(models.Question.id == int(qid))
    if not reqdQuestion:
      abort(404)
    reqdQuestion = reqdQuestion.first()
    # If the <filename> of the question contains link/
    # at the start, replace it with "" and change toDownload
    # flag to flase, render template with link to the link
    # in filename instead of going to /download/<question_id>
    toDownload = True
    if "link/" in reqdQuestion.filename[:5]:
      reqdQuestion.filename = reqdQuestion.filename.replace("link/","")
      app.logger.debug("found link in file, putting link for "+reqdQuestion.filename)
      toDownload = False
    app.logger.debug("Sending Question No "+str(reqdQuestion.id)+" flag: "+reqdQuestion.flag)
    return render_template("question.html",Question=reqdQuestion,toDownload=toDownload)

  elif request.method == "POST":
    # return incorrect answer when no qid is present
    if qid == None:
      return jsonify({'correct' : 0})

    # return 404 when question is not in database
    reqdQuestion = models.Question.query.filter(models.Question.id == int(qid))[0]
    if not reqdQuestion:
      abort(404)

    # return incorrect if flag is not present in form data
    if not request.form.get('flag'):
      return jsonify({'correct' : 0})

    app.logger.debug("Flag Recieved : "+request.form.get("flag")+" For Question "+str(reqdQuestion))

    # check if recieved flag is equal to the flag of the question
    if request.form.get('flag') == reqdQuestion.flag:
      # if the current_user solves question <qid>
      # associate that question with the current_user id
      # using SolvedQuestion(date=dateime.datetime()) Association Object
      # with the current date and time

      solvedQues = models.SolvedQuestion()
      solvedQues.question = reqdQuestion
      current_user.solved_questions.append(solvedQues)
      db_session.commit()

      app.logger.debug(str(current_user)+" Solved Question "+str(reqdQuestion))
      return jsonify({'correct' : 1})

    # else return incorrect answer
    return jsonify({'correct' : 0})

"""
/download/<qid>
send file to download for question with id : qid
"""
@app.route("/download/<int:qid>",methods=["GET","POST"])
@login_required
def download(qid):
    reqdQuestion = models.Question.query.filter_by(id = qid).first()
    if not reqdQuestion:
      abort(404)
    if reqdQuestion.filename == "#":
      abort(404)
    downloads  = os.path.join(app.root_path, app.config['DOWNLOAD_FOLDER'])
    return send_from_directory(directory=downloads, filename=reqdQuestion.filename)

@app.route("/scoreboard",methods=["GET"])
def scoreboard():
  scores = {}
  for user in models.User.query.all():
    scores[user.get_id()] =  { 'username' : user.username, 'score': user.total_score }

  scores = helpers.sortScoreDict(scores)

  return render_template("scoreboard.html",scores=enumerate(scores.items()))

@app.route("/user/<string:username>",methods=["GET"])
def user(username):
  if not models.User.query.filter_by(username=username).first():
    abort(404)

  reqstdUser = models.User.query.filter_by(username=username).first()
  app.logger.debug("Sending Userdata "+str(reqstdUser))
  solvedAnyQuestion = len(reqstdUser.solved_questions)

  return render_template("user.html", reqstdUser=reqstdUser, solvedAnyQuestion=solvedAnyQuestion)

@app.route("/user/",methods=["GET"])
@app.route("/user",methods=["GET"])
def redirect_user():
  if current_user.is_authenticated:
    return redirect("/user/"+current_user.username)
  else:
    return redirect(url_for("home"))    



""" AUTH ROUTES """

"""
/register
template - register.html
"""
@app.route("/register", methods=["GET","POST"])
def register():
  form = RegisterForm()
  if request.method == "GET":
    return render_template("register.html",form = form)
  elif request.method == "POST":
    if form.validate_on_submit():
      if models.User.query.filter_by(username=form.username.data).first():
        user = models.User.query.filter_by(username=form.username.data).first()
        if form.password.data == user.password:
          login_user(user)
          return redirect(url_for("questions"))
        else:
          return render_template("register.html", form=form, message="User Already Exists!")
      else:
        newUser = models.User(username=form.username.data, password=form.password.data)
        app.logger.debug("New User: "+str(newUser))
        db_session.add(newUser)
        db_session.commit()

        login_user(newUser, remember=True)

        return redirect(url_for("questions"))
    else:
      abort(404)

"""
/login
template - login.html
"""
@app.route("/login", methods=["GET","POST"])
def login():
  form = RegisterForm()

  if request.method == 'GET':
      return render_template('login.html', form=form)
  elif request.method == 'POST':
      if form.validate_on_submit():
          user = models.User.query.filter_by(username=form.username.data).first()
          if user:
              if user.password == form.password.data:
                  # correct username+password
                  app.logger.debug("Logging in User: "+str(user))
                  login_user(user, remember=True)
                  dest = request.args.get('next')
                  try:
                    dest_url = url_for(dest)
                  except:
                    return redirect(url_for("questions"))
                  return redirect(dest_url)
              else:
                # incorrect password
                  return render_template("login.html", form=form, message="Incorrect Password!")
          else:
            # user dosen't exist
              return render_template("login.html", form=form, message="Incorrect Username or User Dosen't Exist!")
      else:
        # invalid form
        return render_template("login.html", form=form, message="Invalid Input!")

"""
/logout
"""
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

if __name__ == '__main__':
  init_db()
  app.run(host='0.0.0.0',port=5000)

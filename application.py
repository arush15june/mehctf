from flask import Flask, flash, redirect, render_template, request, url_for, jsonify, abort, send_from_directory
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
import helpers
from functools import reduce
import os
from forms import RegisterForm, ChangePasswordForm
from database import init_db, db_session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import models
import datetime

# Database
init_db()

# App Config

app = Flask(__name__)
app.config['DEBUG'] = False
app.config['DOWNLOAD_FOLDER'] = 'downloads'
app.config['PORT'] = 8080

# Recaptcha Keys

app.config['RECAPTCHA_PUBLIC_KEY'] = '6LcItjUUAAAAAIJnAqsuH3FOJm6mI5Y--ei7JXgl'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6LcItjUUAAAAAHBxk9C_QR6RLn4-49MNPoRDQuOG'

app.secret_key = "m3hCtF"

"""
Admin Views
"""
# Basic Flask-Admin View Model
class CTFView(ModelView):

    def is_accessible(self):    
        return current_user.is_authenticated and current_user.admin

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('login', next=request.url))

# Flask-Admin View For User Model
class UserView(CTFView):
  column_list = ['username', 'password', 'admin']
  column_searchable_list = ['username']
# Flask-Admin View For Question Model
class QuestionView(CTFView):
  column_list = ['id', 'name', 'desc', 'flag', 'points', 'hide']
  column_list = ['id','name','desc','flag','filename']
  
"""
Flask-Admin Config
"""
admin = Admin(app, name='Meh-CTF Admin', template_mode='bootstrap3')
admin.add_view(UserView(models.User, db_session))
admin.add_view(QuestionView(models.Question, db_session))

"""
Flask-Login Config
"""
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(username):
    return models.User.query.filter_by(username = username).first()

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for("login",next=request.endpoint))

"""
SQLAlchemy Flask Config
"""
@app.teardown_appcontext # DB Session Config
def shutdown_session(exception=None):
    db_session.remove()

"""
Flask Config
"""
@app.errorhandler(404)
def page_not_found(e): # Custom 404 Handler
    return render_template('404.html',message="Could Not Find Requested Content"), 404

@app.context_processor
def inject_user(): # Inject user data for the layout in every page
    return dict(user=current_user)
  
@app.template_filter('datetimeformat') # Format DateTime For Scoreboard
def datetimeformat(value, format='%Y/%m/%d %H:%M'):
    return (value+datetime.timedelta(hours=5,minutes=30)).strftime(format)

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
def questions():
  Questions = models.Question.query.all()
  """
  questionSolvedIDs contains IDs of all questions solved by current_user
  """
  questionsSolvedIDs = []
  if current_user.is_authenticated:
    if(len(current_user.solved_questions) > 0):
        questionsSolvedIDs = [solved.question.id for solved in current_user.solved_questions]
  app.logger.debug("Sending Questions: "+str(Questions))

  return render_template('questions.html', Questions=Questions, questionsSolvedIDs=questionsSolvedIDs)

"""
/question/<qid>
Serve the question with id:<qid> + flag checking
template - question.html
"""
@app.route("/question/<qid>", methods=["GET","POST"])
def question(qid = None):
  if request.method == "GET":
    # Question Display Frontend
    if qid == None: # qid is not passed
      abort(404)

    reqdQuestion = models.Question.query.filter(models.Question.id == int(qid))
    if not reqdQuestion: # qid is invalid
      abort(404)
    reqdQuestion = reqdQuestion.first() 
    if reqdQuestion.is_hidden: # Question<qid> is hidden in database
      abort(404)
    # If the <filename> of the question contains link/
    # at the start, replace it with "" and change toDownload
    # flag to flase, render template with link to the link
    # in filename instead of going to /download/<question_id>
    toDownload = True
    if "link/" in reqdQuestion.filename[:5]:
        reqdQuestion.filename = reqdQuestion.filename.replace("link/","")
        app.logger.debug("found link in file, putting link for "+reqdQuestion.filename)
        toDownload = False
        
    solvedByList = []
    for user in models.User.query.all():
        solvedqs = list(filter(lambda sq: sq.question_id == 1, user.solved_questions))
        if(len(solvedqs) == 0):
            continue
        solvedq = solvedqs[0]
        solver = {'username' : solvedq.username, 'solved_on' : solvedq.date}
        solvedByList.append(solver)
    solvedByList = sorted(solvedByList, key=lambda solver: solver['solved_on'])

    app.logger.debug("Sending Question No "+str(reqdQuestion.id)+" flag: "+reqdQuestion.flag)
    return render_template("question.html",Question=reqdQuestion, toDownload=toDownload, solvedByList=solvedByList)

  elif request.method == "POST":
    # Flag Checking Backend
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
    recvdFlag = request.form.get("flag").strip()

    # check if recieved flag is equal to the flag of the question
    if recvdFlag == reqdQuestion.flag:
      # if the current_user solves question <qid>
      # associate that question with the current_user id
      # using SolvedQuestion(date=dateime.datetime()) Association Object
      # with the current date and time

      if current_user.is_authenticated:
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
def download(qid):
    """
      every question contains a parameter called filename,
      which is used to serve files for questions
    """  
    reqdQuestion = models.Question.query.filter_by(id = qid).first()
    if not reqdQuestion:
      abort(404)
    if reqdQuestion.filename == "#":
      abort(404)
    downloads  = os.path.join(app.root_path, app.config['DOWNLOAD_FOLDER'])
    return send_from_directory(directory=downloads, filename=reqdQuestion.filename, as_attachement=True, attachment_filename=reqdQuestion.filename)

@app.route("/scoreboard",methods=["GET"])
def scoreboard():
  """
    Does not display admin users in the scoreboard
  """
  scores = {}
  for user in models.User.query.all():
    if user.is_admin:
      continue
    user.solved_questions = list(filter(lambda x: not x.question.hide, user.solved_questions))
    scores[user.get_id()] =  { 'username' : user.username, 'score': user.total_score, 'last_question_date': user.solved_questions[len(user.solved_questions)-1].date if len(user.solved_questions) > 0 else datetime.datetime.min }

  scores = helpers.sortScoreDict(scores)
  """
    enumerate generates indices(ranks) for the orderedDict
  """
  return render_template("scoreboard.html",scores=enumerate(scores.items()))
"""
/user/<username>
/user/
/user

Serve a user profile with solved questions and change password link for authenticated user
on its own profile
"""
@app.route("/user/<string:username>",methods=["GET"])
def user(username):
  if not models.User.query.filter_by(username=username).first(): # username dosen't exists
    abort(404)

  reqstdUser = models.User.query.filter_by(username=username).first()
  app.logger.debug("Sending Userdata "+str(reqstdUser))
  solvedAnyQuestion = len(reqstdUser.solved_questions) # check if user solved any question
  reqstdUser.solved_questions = helpers.sortSolvedQuesList(reqstdUser.solved_questions)

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
        return render_template("login.html", form=form, message="Invalid Input!")


"""
/logout
"""
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

"""
/change
Change passwords
"""
@app.route("/change", methods=["GET","POST"])
@login_required
def change():
  form = ChangePasswordForm()

  if request.method == "GET":
    return render_template("change.html", form=form)

  elif request.method == "POST":
    oldPass = form.oldpassword.data
    newPass = form.newpassword.data
    newPassReType = form.newpasswordretype.data
    if form.validate_on_submit():
      # Return error if no input is received
      if oldPass is None or newPass is None or newPassReType is None:
        return render_template("change.html",form=form, message="Invalid Input")
      
      # Return error if oldPass dosen't match DB pass
      if not current_user.password == oldPass:
        return render_template("change.html",form=form, message="Incorrect Password")
      
      # Return error if newPass and newPassReType dosen't match
      if not newPass == newPassReType:
        return render_template("change.html",form=form, message="Incorrect Input: Passwords not matching")
  
      current_user.password = newPass
      db_session.commit()
      return render_template("change.html",form=form, message="Password Changed")  

    else:
      return render_template("change.html", form=form, message="Invalid Input")  
      
      
if __name__ == '__main__':
  init_db()
  # Heroku has a DATABASE_URL environment var for the Database URL
  if os.environ.get('DATABASE_URL') is not None:
    app.run(host='0.0.0.0', port=80)
  else:
    app.run(host='0.0.0.0', port=5000)

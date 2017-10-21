from flask import Flask, flash, redirect, render_template, request, url_for, jsonify, abort
import helpers
from forms import RegisterForm
from database import init_db, db_session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import models

# Database
init_db()

# App Config

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['PORT'] = 8080
app.secret_key = "m3hCtF"

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
    return render_template('404.html'), 404

@app.context_processor
def inject_user():
    return dict(user=current_user)

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
  form = RegisterForm()
  return render_template("index.html", form=form)


@app.route('/questions', methods=["GET"])
@login_required
def questions():
  Questions = models.Question.query.all()
  return render_template('questions.html',Questions=Questions)

@app.route("/question/<qno>", methods=["GET","POST"])
@login_required
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

@app.route("/register", methods=["GET","POST"])
def register():
  form = RegisterForm()
  if request.method == "GET":
    return render_template("register.html",form = form)
  elif request.method == "POST":
    if form.validate_on_submit():
      if models.User.query.filter_by(username=form.username.data).first():
        user = models.User.query.filter_by(username=form.username.data).first()
        login_user(user)
        return redirect(url_for("questions"))
      else:
        newUser = models.User(username=form.username.data, password=form.password.data)
        app.logger.debug("New User :"+str(newUser)) 
        db_session.add(newUser)
        db_session.commit()
        
        login_user(newUser)

        return redirect(url_for("questions"))
    else:
      abort(404)

@app.route("/login", methods=["GET","POST"])
def login():
  form = RegisterForm()

  if request.method == 'GET':
      return render_template('login.html', form=form)
  elif request.method == 'POST':
      if form.validate_on_submit():        
          user = models.User.query.filter_by(username=form.username.data).first()
          if user:
              if user.password   == form.password.data:
                # correct username+password
                  app.logger.debug("Logging in User: "+str(user))
                  login_user(user)
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

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

if __name__ == '__main__':
  init_db()
  app.run()
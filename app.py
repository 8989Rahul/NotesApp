from flask import Flask, render_template, flash, redirect, url_for, request, session, logging
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField,TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)


#config mysql
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'NotesApp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#init mysql
mysql = MySQL(app)

Articles = Articles()

# home
@app.route('/')
def index():
    return render_template('home.html')

# about
@app.route('/about')
def about():
    return render_template('/about.html')

# articles
@app.route('/articles')
def articles():
 # create cursor
    cur=mysql.connection.cursor()

    # execute query
    result = cur.execute("select * from articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'Not Found'
        return render_template('articles.html', msg=msg)

    # close connection 
    cur.close()
# single Article
@app.route('/article/<string:id>/')
def article(id):
    # create cursor
    cur=mysql.connection.cursor()

    # execute query
    cur.execute("select * from articles where id = %s", [id])

    article = cur.fetchone()

    return render_template('/article.html' , article=article)

# register form class
class RegisterForm(Form):
    name = StringField('Name',[validators.Length(min=1, max=50)])
    username= StringField('Username',[validators.Length(min=1, max=30)])
    email= StringField('Email',[validators.Length(min=6, max=50)])
    password= PasswordField('password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Password do not match')
    ])
    confirm = PasswordField('confirm Password')

# user register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))      
        
        # create cursor
        cur = mysql.connection.cursor()

        #execute query
        cur.execute("insert into users(name, email, username, password) values(%s, %s, %s, %s) ", (name, email, username, password))

        # commit to db 
        mysql.connection.commit()

        # close connection
        cur.close()

        flash('You are now registerd and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form = form)

#  user login 
@app.route('/login', methods= ['GET' , 'POST'])
def login():
    if request.method == 'POST':
        # get form fields
        username = request.form['username']
        password_candidate = request.form['password']

        #create cursor
        cur = mysql.connection.cursor()

        # get values
        result = cur.execute("select * from users where username = %s", [username])

        if result > 0:
            data = cur.fetchone()
            password = data['password']

            #compare password
            if sha256_crypt.verify(password_candidate, password):
                   #after user logged in
                   #create session
                   session['logged_in'] = True
                   session['username'] = username

                   flash('You are now Logged_In','success')
                   return redirect(url_for('dashboard'))

            else:
                error = 'Password Not Match'
                return render_template('login.html', error = error)       
            # close connection   
            cur.close()

        else:
            error = 'No User Found'
            return render_template('login.html', error = error)    

    return render_template('login.html')

# check if user loggeid in
def is_logged_in(f):
      @wraps(f)
      def wrap(*args , **kwargs):
          if 'logged_in' in session:
              return f(*args , **kwargs)

          else:
              flash('Unauthorised User, Please Log_in', 'danger')
              return redirect(url_for('login'))
      return wrap    


# logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You are now Logout', 'success')
    return redirect(url_for('login'))

# dashboard route
@app.route('/dashboard')
@is_logged_in
def dashboard(): 

    # create cursor
    cur=mysql.connection.cursor()

    # execute query
    result = cur.execute("select * from articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'Not Found'
        return render_template('dashboard.html', msg=msg)

    # close connection 
    cur.close()    


# Article form class
class ArticleForm(Form):
    title = StringField('title',[validators.Length(min=1, max=200)])
    body= TextAreaField('body',[validators.Length(min=30)])

# Add article route
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():   
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # add cursor
        cur = mysql.connection.cursor()

        # execute query
        cur.execute("insert into articles(title, body, author) values(%s, %s, %s)", (title, body, session['username']))
 
        # commit
        cur.connection.commit()

        # close connection
        cur.close()

        flash('Article Created','success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)

# update article route
@app.route('/update_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def update_article(id): 
    # add cursor
    cur = mysql.connection.cursor()

    # execute query
    cur.execute("select * from articles where id = %s",[id])
    
    article = cur.fetchone()

    # get form
    form = ArticleForm(request.form)

    #populate article form field
    form.title.data = article['title']
    form.body.data = article['body']
        
    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # add cursor
        cur = mysql.connection.cursor()

        # execute query
        cur.execute("UPDATE articles SET title=%s, body=%s where id=%s",(title, body, id) )

        # commit
        cur.connection.commit()

        # close connection
        cur.close()

        flash('Article Updated','success')

        return redirect(url_for('dashboard'))

    return render_template('update_article.html', form=form)

@app.route('/delete_article/<string:id>', methods=['post'])
@is_logged_in
def delete_article(id):
    # add cursor
        cur = mysql.connection.cursor()

        # execute query
        cur.execute(" delete from articles where id = %s ", [id])

        # commit
        cur.connection.commit()

        # close connection
        cur.close()

        flash('Article Deleted','success')

        return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.secret_key = 'pass123'
    app.run(debug=True)

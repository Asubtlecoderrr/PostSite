from flask import Flask, render_template,request,json,url_for,session,flash,redirect
from flask_mysqldb import MySQL 
import os
from werkzeug.utils import  secure_filename
from werkzeug.security import generate_password_hash as gen, check_password_hash as check
import math

app = Flask(__name__)

with open('vars.json','r') as v:
    variable = json.load(v)
    
var = variable["variables"]
db_keeps = variable["sql_conf"]


mysql = MySQL(app)

# MySQL Configuration
app.config['MYSQL_HOST'] = db_keeps["mysql_host"]
app.config['MYSQL_USER'] = db_keeps["mysql_user"]
app.config['MYSQL_PASSWORD'] = db_keeps["mysql_password"]
app.config['MYSQL_DB'] = db_keeps["mysql_db"]
app.config['MYSQL_PORT'] = db_keeps['mysql_port']
app.config['UPLOAD_FOLDER'] = var['upload_location']
app.secret_key = os.urandom(24)

@app.after_request
def add_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization, data')
    return response

@app.route("/")
def home():
    return render_template('index.html')

@app.route("/user/login",methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        form = request.form
        email = form['email']
        password = form['password']
        cur = mysql.connection.cursor()
        usercheck = cur.execute("SELECT * FROM user WHERE email=%s", ([email]))
        if usercheck > 0:
            user = cur.fetchone()
            checker = check(user[3], password)
            if checker:
                session['logged_in'] = True
                session['name'] = user[1]
                session['id'] = user[0]
                session['email'] = user[2]
                session['username'] = user[5]
                session['address']= user[-2]
                session['number']=user[-1]
                session['desc']=user[4]
                flash(f"Welcome {session['name']}!! Your Login is Successful", 'success')
                return redirect ('/user/{}'.format(session['username']))
            else:
                cur.close()
                flash('Wrong Password!! Please Check Again.', 'danger')
                return render_template('login.html')
            
        else:
            cur.close()
            flash('User Does Not Exist!! Please Enter Valid details.', 'danger')
            return render_template("login.html")
        cur.close()
       
        
    return render_template("login.html")

@app.route("/user/register", methods=['GET', 'POST'])
def customer_register():
    if request.method == 'POST':
        form = request.form
        email = form['email']
        name = form['name']
        address = form['address']
        number = form['number']
        password = gen(form['pass'])
        username = form['username']
        desc = form['desc']
        cur = mysql.connection.cursor()
        usercheck = cur.execute("SELECT * FROM user;")
        if usercheck>0:
            users = cur.fetchall()
            for user in users:
                if user[2] == email:
                    flash("User Already Exists!, Please Login...","danger")
                    return redirect('/user/login')
                elif user[5]==username:
                    flash("Username Already Exists! Try different..","danger")
                    return redirect('/user/register')
        cur.execute("INSERT INTO user (name,email,password,description,username,address,number) values (%s,%s,%s,%s,%s,%s,%s);", (name,email,password,desc,username,address,number))
        mysql.connection.commit()
        cur.close()
        flash("Registration Successful !! Please Login To Continue","success")
        return redirect('/user/login')
    return render_template("register.html")

@app.route('/user/<string:username>', methods=['GET','POST'])
def showProfile(username):
        username = username
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM user where username=%s",([username]))
        profile=cur.fetchone()
        return render_template('profile.html',profile=profile)
    

@app.route("/update/user/", methods=['GET','POST'])
def update_profile():
    if 'id' in session:
        if request.method == 'POST':
            form = request.form
            description = form['desc']
            name=form['name']
            email=form['email']
            number = form['number']
            address=form['address']
            
            cur = mysql.connection.cursor()
            cur.execute("UPDATE user SET description = %s, name=%s, address=%s, email=%s, number=%s where username=%s",([description,name,address,email,number,session['username']]))
            mysql.connection.commit()
            cur.close()
            session['name'] = name
            session['email'] = email
            session['address']= address
            session['number']=number
            session['desc']=description
            flash('Saved your details','success')
            return redirect(f"/user/{session['username']}")

        else:
            return render_template('edit.html')
    flash('You Are Not Signed In, Please Sign In First','danger')
    return redirect("/user/login")

@app.route('/myposts/<int:id>')
def me(id):
    if 'id' in session:
        id=id
        cur = mysql.connection.cursor()
        q = cur.execute("SELECT user.name, posts.title, posts.text , DATE(posts.upload_date)  FROM user , posts WHERE user.id=%s and posts.user_id=%s;",([id,id]))
        
        if q > 0:
            myposts = cur.fetchall()
            return render_template('myposts.html', posts=myposts)
        return render_template('myposts.html')
    flash('You Are Not Signed In, Please Sign In First','danger')
    return redirect("/user/login")


@app.route("/create", methods=['GET','POST'])
def create_new_post():
    if ('id' in session):
        if (request.method == 'POST'):
            form = request.form
            title = form['title']
            text = form['text']
            user_id = session['id']
            name = session['name']
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO posts(text,user_id,title, name) VALUES(%s, %s, %s, %s);", ([text,user_id,title, name]))
            mysql.connection.commit()
            cur.close()
            flash("Blog Posted Successfully", "success")
            return redirect('/home')    
        return render_template('create.html')
    flash('You Are Not Signed In, Please Sign In First','danger')
    return redirect("/user/login")
  

@app.route('/home')
def get_all():
    if 'id' in session:
        cur = mysql.connection.cursor()
        q = cur.execute("SELECT posts.*,DATE(posts.upload_date),user.username FROM posts ,user where user.id=posts.user_id ;")
        if q > 0:
            posts = cur.fetchall()
            return render_template('home.html', posts=posts)
        return render_template('home.html')
    flash('You Are Not Signed In, Please Sign In First','danger')
    return redirect("/user/login")


@app.route('/post/<int:id>/')
def post(id):
    if 'id' in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM posts WHERE post_id={};".format(id))
        info = cur.fetchone()
        return render_template('post.html', info=info)
    flash('You Are Not Signed In, Please Sign In First','danger')
    return redirect("/user/login")

@app.route("/logout")
def logout():
    if 'id' in session:
        session['logged_in'] = False
        session.pop('name') 
        session.pop('id') 
        session.pop('username') 
        session.pop('email')
        flash('User Logged Out','success')
        return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)

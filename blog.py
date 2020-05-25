from flask import Flask, redirect,url_for,render_template, request,session # imoporting class Flask from module class
from flask_sqlalchemy import SQLAlchemy
import json
from werkzeug.utils import secure_filename
from flask_mail import Mail
import math
from datetime import datetime
import os


with open('config.json','r') as c:
    parameters = json.load(c)["params"]

local_server = True
Encrypted_visions = Flask(__name__)
Encrypted_visions.secret_key = 'supersecretkey'
Encrypted_visions.config['Upload_Folder'] = parameters['upload_location']
Encrypted_visions.config.update(
      MAIL_SERVER = 'smtpout.secureserver.net',
      MAIL_PORT = '465',
      MAIL_USE_SSL = True,
      MAIL_USERNAME = parameters["mail_user"],
      MAIL_PASSWORD = parameters["mail_pwd"]
)
mail = Mail(Encrypted_visions)
if local_server:
    Encrypted_visions.config['SQLALCHEMY_DATABASE_URI'] = parameters["local_uri"]
else:
    Encrypted_visions.config['SQLALCHEMY_DATABASE_URI'] = parameters["prod_uri"]
db = SQLAlchemy(Encrypted_visions)

class contacts(db.Model):
    Sno = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(80), unique=False, nullable=False)
    Date = db.Column(db.String(120), unique=False, nullable=True)
    Email_Address = db.Column(db.String(120), unique=False, nullable=False)
    Phone_Number = db.Column(db.String(120), unique=False, nullable=False)
    Message = db.Column(db.String(120), unique=False, nullable=False)

class Posts(db.Model):
    Sno = db.Column(db.Integer,primary_key=True)
    Title = db.Column(db.String(100), unique = False, nullable=False)
    slug = db.Column(db.String(25), unique=True,nullable=False)
    Content = db.Column(db.String(500),unique=True,nullable=False)
    Date = db.Column(db.String(120),unique=False,nullable=True)
    img_file = db.Column(db.String(25),unique = True, nullable = False)
    sub_heading = db.Column(db.String(30),unique = True , nullable=False)
@Encrypted_visions.route("/")
def home():
    post2 = Posts.query.filter_by().all()
    last = math.ceil(len(post2)/int(parameters['no. of posts'   ]))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    post2 = post2[(page-1)*int(parameters['no. of posts']):(page-1)*int(parameters['no. of posts'])+int(parameters['no. of posts'])]
    # [0: parameters["no. of posts"]]

    if (page==1):
        prev = "#"
        next = "/?page="+ str(page+1)
    elif (page==last):
        next = "#"
        prev = "/?page="+ str(page-1)
    else:
        next = "/?page="+str(page+1)
        prev = "/?page="+ str(page-1)


    return render_template('index.html', parameters=parameters, post2=post2, prev=prev, next=next)

@Encrypted_visions.route("/post/<string:post_slug>",methods = ['GET'])
def post_route(post_slug):
    post1 = Posts.query.filter_by(slug=post_slug).first()# to go in database and search for slug we have passed with /
    return render_template('post.html', parameters=parameters, post1=post1)
@Encrypted_visions.route("/about")
def about():
    return render_template('about.html', parameters=parameters)

@Encrypted_visions.route("/contact", methods = ['GET','POST'],)
def contact():
    if(request.method == 'POST'):
        '''add entry to data base'''
        Name = request.form.get('Name')
        Email = request.form.get('Email')
        Phone = request.form.get('Phone')
        Date = request.form.get('Date')
        Message = request.form.get('Message')

        entry =contacts(Name = Name, Email_Address = Email, Date = Date,Phone_Number = Phone, Message = Message)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New Message From' + Name,sender=Email, recipients=[parameters["mail_user"]],body = Message +"\n"+ Phone)

    return render_template('contact.html', parameters=parameters)
@Encrypted_visions.route("/dashboard", methods = ['GET','POST'])
def dashboard():
    if ('user' in session and session['user'] == parameters['admin_user']):
        posts = Posts.query.all()
        return render_template('dashboard.html',parameters=parameters,posts = posts)
    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if (username == parameters['admin_user'] and userpass == parameters['admin_password']):
            #set the session variable
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html',parameters=parameters,posts = posts)
    return render_template('login.html',parameters=parameters)
# if user is already logged in , he will not send post request then

@Encrypted_visions.route("/edit/<string:sno>",methods = ['POST','GET'])
def edit(sno):
    if ('user' in session and session['user'] == parameters['admin_user']):
        if request.method == 'POST':
            title = request.form.get('title')
            subheading = request.form.get('subheading')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if sno == '0':
                post = Posts(Title = title, slug = slug, Content = content, img_file = img_file, sub_heading = subheading,Date = date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(Sno=sno).first()
                post.Title = title
                post.slug = slug
                post.Content = content
                post.img_file = img_file
                post.sub_heading = subheading
                post.Date = date
                db.session.commit()
                return redirect('/edit/'+sno)
        post = Posts.query.filter_by(Sno=sno).first()
        return render_template('edit.html',parameters=parameters,post=post,Sno=sno)
    else:
        return render_template('login.html', parameters=parameters)

@Encrypted_visions.route("/uploader",methods = ['POST','GET'])
def uploader():
    if ('user' in session and session['user'] == parameters['admin_user']):
        if request.method == 'POST' :
            f = request.files['file1']
            f.save(os.path.join(Encrypted_visions.config['Upload_Folder'], secure_filename(f.filename) ))
            return "Uploaded Successfully"

@Encrypted_visions.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

@Encrypted_visions.route("/delete/<string:sno>",methods = ['POST', 'GET'])
def delete(sno):
    if ('user' in session and session['user'] == parameters['admin_user']):
        post = Posts.query.filter_by(Sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')


Encrypted_visions.run(debug=True,port = 5000)

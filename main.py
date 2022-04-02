from flask import Flask,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_mail import Mail
import json
import math
import os
# import socket
# socket.getaddrinfo('localhost', 8080)
with open('credentials.json','r') as b:
    data=json.load(b)

with open('config.json','r') as c:
    params=json.load(c)["params"]

local_server=True
app = Flask(__name__)
app.secret_key = 'SECRET KEY'
app.config['UPLOAD_FOLDER']=params['up_loc']
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail=Mail(app)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

if(local_server):
   app.config["SQLALCHEMY_DATABASE_URI"] = params["local_uri"]
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params["prod_uri"]


db = SQLAlchemy(app)

class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50),nullable=False)
    phone_num = db.Column(db.String(12),nullable=False, unique=True)
    msg = db.Column(db.String(120),nullable=False)
    date = db.Column(db.String(30),nullable=True)
    email= db.Column(db.String(20),nullable=False, unique=True)

class Posts(db.Model):
        sno = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(50), nullable=False)
        slug = db.Column(db.String(50), nullable=False)
        content = db.Column(db.String(120), nullable=False)
        tagline = db.Column(db.String(120), nullable=False)
        date = db.Column(db.String(30), nullable=True)
        img_file = db.Column(db.String(50), nullable=True)
        author = db.Column(db.String(120), nullable=True)


@app.route('/')
def home():
    posts = Posts.query.filter_by().all()
    # [0: params['no_of_posts']]
    last=math.ceil(len(posts)/int(params['no_of_posts']))

    page=request.args.get('page')
    if(not str(page).isnumeric()):
        page=1
    page=int(page)
    posts=posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+int(params['no_of_posts'])]

    if(page==1):
        prev= "#"
        next= "/?page=" + str(page + 1)

    if(page==last):
        prev = "/?page=" + str(page - 1)
        next = "#"

    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)




    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)
@app.route('/about')
def about():
    return render_template('about.html',params=params)

@app.route('/dashboard',methods=['GET','POST'])
def dashboard():
    username=None
    userpass=None
    if ('user' in session and session['user'] == params['admin_user']):
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params,posts=posts)
    if request.method=='POST':
        username=request.form.get('uname')
        userpass = request.form.get('pass')

    # username='uname'
    # userpass='pass'
    if(username==params['admin_user'] and userpass==params['admin_password']):
        session['user']=username
        posts=Posts.query.all()
        return render_template('dashboard.html', params=params,posts=posts)

    return render_template('login.html',params=params)

@app.route('/add/<string:sno>',methods=['GET','POST'])
def add(sno):

    if ('user' in session and session['user'] == params['admin_user']):
        if request.method=='POST':
            box_title=request.form.get('title')
            tagline=request.form.get('tagline')
            slug=request.form.get('slug')
            content=request.form.get('content')
            img_file=request.form.get('img_file')
            date=datetime.now()
            # post = None
            if sno=='0':
                post=Posts(title=box_title, slug=slug, tagline=tagline, content=content, img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()

            else:
                post=Posts.query.filter_by(sno=sno).first()
                post.title=box_title
                post.slug=slug
                post.tagline=tagline
                post.content=content
                post.img_file=img_file
                post.date=date
                db.session.commit()
                return redirect('/add/'+sno)
        post = Posts.query.filter_by(sno=sno).first()
        return render_template('add.html', params=params, post=post,sno=sno)


@app.route('/upload',methods=['GET','POST'])
def upload():
    if ('user' in session and session['user'] == params['admin_user']):
        if (request.method == 'POST'):
            fl=request.files['file1']
            fl.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(fl.filename)))
            return "Your file has been uploaded successfully"


@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')


@app.route('/delete/<string:sno>',methods=['GET','POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        post=Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')


@app.route('/contact',methods=['GET','POST'])
def contact():
    if(request.method=='POST'):
        ''' Add entry to the database'''
        name=request.form.get('name')
        email=request.form.get('email')
        phone=request.form.get('phone')
        message=request.form.get('message')
        entry = Contact(name=name, email=email, phone_num=phone, msg=message, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message(' Here is the message from' + name,
                           sender=email,
                           recipients=[params['gmail-user']],
                           body= message + "\n" + phone)
    return render_template('contact.html',params=params)
@app.route('/post/<string:post_slug>', methods=['GET'])
def post_route(post_slug):
    post=Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html',params=params,post=post)

@app.route('/create',methods=['GET','POST'])
def create():
    username=None
    userpass=None
    for item in data['credentials']:
      print('hello')
      print(request.method)
      if ('user' in session and session['user'] == item['username']):
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params,posts=posts)
      if (request.method=='POST'):
        print('hi')
        username=request.form.get('uname')
        userpass = request.form.get('pass')

    # username='uname'
    # userpass='pass'

     # if(username==params['admin_user'] and userpass==params['admin_password']):
     #    session['user']=username
     #    posts=Posts.query.all()
     #    return render_template('create.html', params=params,posts=posts)
    print(username)
    print(userpass)
    for obj in data['credentials']:
         print(obj["username"], obj["password"], sep=' ')
         if (username == obj["username"] and userpass == obj["password"]):
             session['user'] = username
             posts = Posts.query.all()
             return render_template('create.html', params=params, posts=posts)

    return render_template('login.html',params=params)

@app.route('/add/<string:sno>',methods=['GET','POST'])
def add1(sno):
  for item in data['credentials']:
    if ('user' in session and session['user'] == item['username']):
        if request.method=='POST':
            box_title=request.form.get('title')
            tagline=request.form.get('tagline')
            slug=request.form.get('slug')
            content=request.form.get('content')
            img_file=request.form.get('img_file')
            date=datetime.now()
            # post = None
            if sno=='0':
                post=Posts(title=box_title, slug=slug, tagline=tagline, content=content, img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()

            else:
                post=Posts.query.filter_by(sno=sno).first()
                post.title=box_title
                post.slug=slug
                post.tagline=tagline
                post.content=content
                post.img_file=img_file
                post.date=date
                db.session.commit()
                return redirect('/add/'+sno)
        post = Posts.query.filter_by(sno=sno).first()
        return render_template('add.html', params=params, post=post,sno=sno)


app.run(debug=True)

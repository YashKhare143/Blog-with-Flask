from flask import Flask, render_template, request, session,redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from werkzeug.utils import secure_filename
import math
import os
from flask_mail import Mail


with open('Y:\\Proagraming\\Python\\Flask\\templates\\config.json','r') as c:
    params = json.load(c)["params"]

local_server = True
app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIl_PORT = '465',
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-pass'],
)
mail = Mail(app)

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)


class Contacts(db.Model):
    '''
    sno, name phone_num, msg, date, email
    '''
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    mes = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)

class Post(db.Model):
    '''
    sno, name phone_num, msg, date, email
    '''
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(12), nullable=False)
    content = db.Column(db.String(1024), nullable=False)
    tagline = db.Column(db.String(1024), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img = db.Column(db.String(12), nullable=True)
  
                        # home
@app.route("/")
def home():
    posts = Post.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))

    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page - 1)*int(params['no_of_posts']): (page - 1)*int(params['no_of_posts']) + int(params['no_of_posts'])]

    if (page == 1):
        prev = "#"
        next = "/?page="+ str(page+1)
    elif (page == last):
        prev = "/?page="+ str(page-1)
        next = "#"
    else:
        prev = "/?page="+ str(page-1)
        next = "/?page="+ str(page+1)


    return render_template('index.html', params = params, posts = posts,page = page,last = last,prev = prev,next = next)
    
                         # deleat
@app.route("/delete/<string:sno>", methods = ['GET', 'POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        post = Post.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/login')
                        #  ulpoader
@app.route("/uploader", methods = ['GET' , "POST"] )
def upload():

    if ('user'  in session and session['user'] == params['admin_user']):

        if(request.method=='POST'):

           f = request.files['file']
           f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
           return 'upload successfully'

                        # about
@app.route("/about")
def about():
    return render_template('about.html', params = params)

                        # logout
@app.route("/logout")
def logout():
    if ('user'  in session and session['user'] == params['admin_user']):
       session.pop('user', None)
       posts = Post.query.filter_by().all()[0:params['no_of_posts']]
       return render_template('index.html', params = params, posts = posts, )
  
                        # login
@app.route("/login", methods = ['GET' , "POST"])
def login():
    if ('user' in session and session['user'] == params['admin_user']):
        posts = Post.query.all()
        return render_template('dashboard.html', params = params, posts = posts)

    if request.method=='POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if (username == params['admin_user'] and  password == params['admin_pass']):
            # set the session variable
            session['user'] = username
            posts = Post.query.all()
            return render_template('dashboard.html', params = params, posts = posts)
            # redirect to admin panel
    return render_template('login.html', params = params)

                    # posts in dashboard
@app.route("/post/<string:post_slug>", methods = ['GET'])
def post(post_slug):
    post = Post.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params = params, post=post)

                        # edit



@app.route("/edit/<string:sno>", methods = ['GET', 'POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            date = datetime.now()
            img = request.form.get('img_file')

            if sno == '0':
                post = Post(title=box_title, slug = slug, content = content,tagline = tline, date = date, img = img)
                db.session.add(post)
                db.session.commit()
                
            else:
                post = Post.query.filter_by(sno=sno).first()
                post.title = box_title
                post.slug = slug
                post.content = content
                post.tagline = tline
                post.img = img
                post.date = date
                db.session.commit()
                return redirect('/edit/'+sno)
        post = Post.query.filter_by(sno=sno).first()
        return render_template('edit.html', params = params, post = post, sno = sno)

                        # contact
@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        '''Add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, phone_num = phone, mes = message, date= datetime.now(),email = email )
        db.session.add(entry)
        db.session.commit()

        mail.send_message('New message from' + name,
                           sender = email,
                           recipients = [params['gmail-user']],
                           body = message + "\n" + phone)
    return render_template('contact.html', params = params)


app.run(debug=True)


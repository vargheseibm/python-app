from flask import Flask, render_template, redirect, url_for, flash,request
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm,LoginForm,CommentForm
from flask_gravatar import Gravatar
from functools import wraps
from flask import abort

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)
gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:\\Data\\Learning\\Python_100DayChallenge\\Python\\intermediate\\Day69\\Starting+Files+-+blog-with-users-start\\blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


##CONFIGURE TABLES

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    
    #Create Foreign Key, "users.id" the users refers to the tablename of User.
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))   # This add a new column to DB table
    #Create reference to the User object, the "posts" refers to the posts protperty in the User class.
    author = relationship("User", back_populates="posts")
    
    
    
    #author = db.Column(db.String(250), nullable=False)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    #***************Parent Relationship*************#
    comments = relationship("Comment", back_populates="parent_post")

#Create the User Table
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    
    posts = relationship("BlogPost",back_populates="author")
     #*******Add parent relationship*******#
    #"comment_author" refers to the comment_author property in the Comment class.
    comments = relationship("Comment",back_populates="comments_author")
    
class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text =  db.Column(db.Text, nullable=False)
    
        
    #*******Add child relationship*******#
    #"users.id" The users refers to the tablename of the Users class.
    #"comments" refers to the comments property in the User class.
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comments_author = relationship("User",back_populates="comments")
    
     #***************Child Relationship*************#
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")
    
    
# Create all the tables in the database
with app.app_context():
     db.create_all()
 
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


#Create admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        #Otherwise continue with the route function
        return f(*args, **kwargs)        
    return decorated_function
  
  
@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts,current_user=current_user)


@app.route('/register', methods=["GET","POST"])
def register():
    form = RegisterForm()
  
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        
        if  user:
            flash("email already registered, Please login")
            return redirect(url_for('login'))
        
       
        password = generate_password_hash(form.password.data,method='pbkdf2:sha256',salt_length=8)
        new_user = User(name=name, email=email,password=password)
        db.session.add(new_user)
        db.session.commit()
            #This line will authenticate the user with Flask-Login
        login_user(new_user)
        return redirect(url_for('get_all_posts'))
      
           
    return render_template("register.html",form=form,current_user=current_user)


@app.route('/login', methods=["GET","POST"])
def login():
    
    form = LoginForm()
    email = form.email.data
    password = form.password.data
    
    if form.validate_on_submit():
              
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash("username/password incorrect, retry")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password , password):
            flash("username/password incorrect, retry")
            return redirect(url_for('login'))
            
        else: 
            login_user(user)
            return redirect(url_for('get_all_posts'))
            
    
    return render_template("login.html",form=form,current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>",methods=["GET","POST"])
def show_post(post_id):
    form= CommentForm()
    requested_post = BlogPost.query.get(post_id)
    
    
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for('login'))
        comments = form.comments.data
        new_comment = Comment(text=comments,comments_author = current_user,parent_post = requested_post)
        db.session.add(new_comment)
        db.session.commit()
        comments_list = Comment.query.filter_by(parent_post=requested_post).first()
        return render_template("post.html", post=requested_post,form=form)

    return render_template("post.html", post=requested_post,current_user=current_user,form=form)
    




@app.route("/about")
def about():
    return render_template("about.html",current_user=current_user)


@app.route("/contact")
def contact():
    return render_template("contact.html",current_user=current_user)


@app.route("/new-post", methods=["GET","POST"])
# Mark this decorator
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            #author=form.author.data,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form,current_user=current_user)


@app.route("/edit-post/<int:post_id>", methods=["GET","POST"])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=current_user,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form,is_edit=True, current_user=current_user)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

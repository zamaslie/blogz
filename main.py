from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:blogz@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key='butthole'

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(1000))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner=owner

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password

@app.before_request
def require_login():
    print(request.endpoint)
    allowed_routes = ['login_user', 'add_user', 'show_blog', 'index', 'static']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

@app.route('/', methods=['GET'])
def index():
    all_users = User.query.all()
    return render_template('index.html', list_all_users=all_users)


@app.route('/blog', methods=['GET'])
def show_blog():
    posts= Blog.query.all()
    post_id = request.args.get('id')
    single_user_id = request.args.get('user')
    
    if post_id:
        single_post = Blog.query.get(post_id)
        return render_template('single_post.html', single_post=single_post)
    else:
        if single_user_id:
            posts = Blog.query.filter_by(owner_id=single_user_id)
            user=User.query.filter_by(id=single_user_id)
            return render_template('singleuser.html', posts=posts, user=user)

    return render_template('blog.html', posts=posts)



def empty_val(x):
    if x:
        return True
    else:
        return False

    
@app.route('/newpost', methods=['POST', 'GET'])
def create_new_post():
    if request.method == 'POST':

        post_title = request.form['title']
        post_entry = request.form['body']
        owner = User.query.filter_by(username=session['username']).first()
        post_new = Blog(post_title, post_entry, owner)

        if empty_val(post_title) and empty_val(post_entry): 
            db.session.add(post_new)
            db.session.commit()
            post_link = "/blog?id=" + str(post_new.id)
            return redirect('/blog')
        else:
            if not empty_val(post_title) and not empty_val(post_entry):
                flash('Please enter a title and blog entry', 'error')
                return render_template('new_post.html', post_title=post_title, post_entry=post_entry)
            elif not empty_val(post_title):
                flash('Please enter a title', 'error')
                return render_template('new_post.html', post_entry=post_entry)
            elif not empty_val(post_entry):
                flash('Please enter a blog entry', 'error')
                return render_template('new_post.html', post_title=post_title)

    else:
        return render_template('new_post.html')

@app.route('/signup', methods=['POST', 'GET'])
def add_user():

    if request.method == 'POST':

        user_name = request.form['username']
        user_password = request.form['password']
        user_password_validate = request.form['password_validate']


        if not empty_val(user_name) or not empty_val(user_password) or not empty_val(user_password_validate):
            flash('All fields must be filled in', 'error')
            return render_template('signup.html')

        if user_password != user_password_validate:
            flash('Passwords must match', 'error')
            return render_template('signup.html')

        if len(user_password) < 3 and len(user_name) < 3:
            flash('Username and password must be at least three characters', 'error')
            return render_template('signup.html')

        if len(user_password) < 3:
            flash('Password must be at least three characters', 'error')
            return render_template('signup.html')

        if len(user_name) < 3:
            flash('Username must be at least three characters', 'error')
            return render_template('signup.html')

        existing_user = User.query.filter_by(username=user_name).first()
        if not existing_user: 
            user_new = User(user_name, user_password) 
            db.session.add(user_new)
            db.session.commit()
            session['username'] = user_name
            flash('New user created', 'success')
            return redirect('/newpost')
        else:
            flash('Error, there is an existing user with the same username', 'error')
            return render_template('signup.html')

    else:
        return render_template('signup.html')
 
@app.route('/login', methods=['POST', 'GET'])
def login_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username and not password:
            flash('Username and password cannot be blank', 'error')
            return render_template('login.html')
        if not username:
            flash('Username cannot be blank', 'error')
            return render_template('login.html')
        if not password:
            flash('Password cannot be blank', 'error')
            return render_template('login.html')
        

        user = User.query.filter_by(username=username).first()

        if not user:
            flash('Username does not exist', 'error')
            return render_template('login.html')
        
        if user.password != password:
            flash('Password is incorrect', 'error')
            return render_template('login.html')

        
        if user and user.password == password:
            # saves username to session
            session['username'] = username
            return redirect('/newpost')


    return render_template('login.html')

@app.route('/logout')
def logout():
    del session['username']
    flash('You are logged out', 'success')
    return redirect('/blog')

if __name__ == '__main__':
    app.run()

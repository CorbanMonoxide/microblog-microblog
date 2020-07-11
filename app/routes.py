from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm, \
    EmptyForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import User, Post
from app.email import send_password_reset_email
from datetime import datetime


#Routes for users to take around the website
#Will validate clicks and inputs and direct to html pages

#BEFORE_REQUEST
#Check last seen time and registers it in the database
@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


#INDEX
#This route is for the index page or homepage that will display followed posts
@app.route('/', methods = ['GET', 'POST'])
@app.route('/index', methods = ['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type = int)
    posts = current_user.followed_posts().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('index', page = posts.next_num) \
        if posts.has_next else None #next_url takes you to next page only if one exists
    prev_url = url_for('index', page = posts.prev_num) \
        if posts.has_prev else None #prev_url takes you to previous page only if one exists
    return render_template('index.html', title='Home', form=form,  
                            posts=posts.items, next_url = next_url,
                            prev_url = prev_url)


#FOLLOW
#This route will allow users to follow other users
@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm() # Measure to protect against CSRF attacks
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not fount.'.format(username))
            return redirect(url_for('index'))
        
        if user == current_user:
            flash('You are already following yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are following {}!'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


#UNFOLLOW
#This Route will allow users to unfollow other users
@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are no longer following {}.'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


#LOGIN
#This route logs in a user
#It checks username and password information against the DB
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: #Authenticated users get directed to Index after logging in
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit(): #If form is entered to validate
        user = User.query.filter_by(username=form.username.data).first() #query's username
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login')) #If not authenticated bring back to login fields
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


#LOGOUT
#This route logs the user out
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


#REGISTER
#This route allows for users to register
#This route also creates db entrys for new users
#It checks for duplicates and does not allow them.
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


#RESET PASSWORD REQUEST
#This route will allow users to reset their password
@app.route('/reset_password', methods = ['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for password reset instructions')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                            title='Reset Password', form=form)


#RESET PASSWORD
#This route allows a user with the liink to reset their password
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


#USER
#This route takes care of the User's Page
@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type = int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username = user.username, page = posts.next_num)\
        if posts.has_next else None
    prev_url = url_for('user', username = user.username, page = posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items,
                            next_url = next_url, prev_url = prev_url, form = form)


#EDIT_PROFILE
 #This is the route to get to the profile edit page
@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form = form)


#EXPLORE
#This route will describe the explore page
@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type = int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('explore', page = posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('explore', page = posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title = 'Explore', posts = posts.items,
                            next_url = next_url, prev_url = prev_url)
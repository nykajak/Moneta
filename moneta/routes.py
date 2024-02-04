from flask import request,render_template,flash,redirect,url_for
from moneta import app,db,bcrypt,login_manager
from moneta.forms import MyLoginForm,MyRegistrationForm,SearchForm
from moneta.models import User,Section,Book,Author
from flask_login import login_user,logout_user,login_required,current_user

## Utility functions!

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()

@app.errorhandler(404)
def page_not_found(e):
    app.logger.critical("Expected page does not exist!")
    return "Page not found",404

@app.route("/test")
def test():
    return render_template("base_templates/test.html",user = current_user)


## Decision routes
@app.route("/")
def home():
    return render_template("base_templates/home.html",user=current_user)

## Anon user routes

@app.route("/login",methods=['GET','POST'])
def login():
    form = MyLoginForm()

    if form.validate_on_submit():
        app.logger.info("Login form validated!")
        
        u = User.query.filter_by(email=form.email.data).first()
        app.logger.debug("User query processed!")

        if u and bcrypt.check_password_hash(u.password,form.password.data):
            app.logger.debug("Successful login!")
            res = login_user(u)
            app.logger.debug(f"Result of logging in is: {res}")

            next = request.args.get('next')
            return redirect(next or url_for('home'))

        else:
            if not u:
                app.logger.debug("No such user!")
                flash("No such user found!",category="danger")
            else:
                app.logger.debug("User provided incorrect password!")
                flash("Incorrect password!",category="danger")

    return render_template("anon_specific/login.html",login_user_form = form)


@app.route("/register",methods=['GET','POST'])
def register():
    form = MyRegistrationForm()

    if form.validate_on_submit():
        app.logger.info("Register form validated!")

        hashed_password = bcrypt.generate_password_hash(form.password.data)
        u = User(username=form.username.data,email=form.email.data,password=hashed_password)
        app.logger.debug("User query processed!")

        flag = 0
        try:
            db.session.add(u)
            db.session.commit()
            flag = 1

        except Exception as E:
            failed = E.args[0][56:]
            if failed == 'email':
                app.logger.debug("User not created as email already exists!")
                flash("Email already in use",category='danger')
            elif failed == 'username':
                app.logger.debug("User not created as username already exists!")
                flash("Username already in use",category='danger')
                

        if flag:
            app.logger.debug("User created!")
            res = login_user(u)
            app.logger.debug(f"Result of logging in is: {res}")
            app.logger.debug("User logged in!")

            next = request.args.get('next')
            return redirect(next or url_for('home'))
        else:
            pass   

    return render_template("anon_specific/register.html",register_user_form = form)

## Normal user routes.

# Logout
@app.route("/logout")
def logout():
    logout_user()
    app.logger.debug("User logged out!")
    return redirect(url_for('home'))

# Genre
@app.route("/sections")
@login_required
def genre():
    sections = Section.query.all()
    return render_template('user_specific/sections.html',sections=sections, user=current_user)

@app.route("/sections/<name>")
@login_required
def selected_genre(name):
    section = Section.query.filter(Section.name == name.title()).one()
    return render_template('user_specific/genre_list.html',genre = name.title(), books=section.books, user=current_user)

# Shelf
@app.route("/shelf")
@login_required
def shelf():
    books = [borrow_obj.book for borrow_obj in current_user.borrowed]
    return render_template('user_specific/shelf.html',books=books, user=current_user)

# Book
@app.route("/book/<id>")
@login_required
def selected_book(id):
    curr_book = Book.query.filter(Book.id == id).one()
    
    your_score = None
    avg_score = None
    sum_score = 0

    all_ratings = curr_book.ratings
    all_authors = curr_book.authors
    all_sections = curr_book.sections

    for user_rating in all_ratings:
        if user_rating.user_id == current_user.id:
            your_score = user_rating.score

        sum_score += user_rating.score

    if (sum_score != 0):
        avg_score = sum_score / len(all_ratings)

    return render_template('user_specific/book.html',book=curr_book, user=current_user,
                            avg_score = avg_score, your_score = your_score,
                            num_scores = len(all_ratings), all_authors = all_authors,
                            all_sections = all_sections)

@app.route("/read/<id>")
@login_required
def read(id):
    return render_template("user_specific/read.html",user=current_user)
    
# Author
@app.route("/author/<id>")
@login_required
def selected_author(id):
    author = Author.query.filter(id == Author.id).one()
    books = author.books
    return render_template('user_specific/author.html',author=author,books=books,user=current_user)

# Search
@app.route("/explore", methods=['GET','POST'])
@login_required
def search():
    form = SearchForm()

    if form.validate_on_submit():
        book_name,author_name,section_name = form.book_name.data,form.author_name.data,form.section_name.data
        result = Book.query.filter(Book.name.ilike(f"%{book_name}%"))
        result = result.filter(Book.authors.any(Author.name.ilike(f"%{author_name}%")))
        result = result.filter(Book.sections.any(Section.name.ilike(f"%{section_name}%")))

        result = list(result)
        result.sort()
        return render_template("user_specific/results.html",user=current_user, results = result)

    return render_template("user_specific/explore.html",user=current_user,form = form)
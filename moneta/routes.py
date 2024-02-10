from flask import request,render_template,flash,redirect,url_for
from moneta import app,db,bcrypt,login_manager
from moneta.forms import *
from moneta.models import User,Section,Book,Author
from flask_login import login_user,logout_user,login_required,current_user
from functools import wraps

## Utility functions!

# Helper function called internally to login correct user.
@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()

# Helper function called internally to display content for pages that do not exist.
@app.errorhandler(404)
def page_not_found(e):
    app.logger.critical("Expected page does not exist!")
    return "Page not found",404

# Helper wrapper to ensure that only librarians can access certain pages.
def librarian_required(fun):
    @wraps(fun)
    def inner(*args,**kwargs):
        if not current_user.is_anonymous and current_user.is_librarian:
            return fun(*args,**kwargs)
        else:
            return app.login_manager.unauthorized()
    return inner

# Helper wrapper to ensure that only normal users can access certain pages.
def normal_user_required(fun):
    @wraps(fun)
    def inner(*args,**kwargs):
        if not current_user.is_anonymous and not current_user.is_librarian:
            return fun(*args,**kwargs)
        else:
            return app.login_manager.unauthorized()
    return inner    

# Route that reroutes user to their profile page if logged in, the about page if not.
@app.route("/")
def home():
    return render_template("base_templates/home.html")

## Anon user routes

# Route that renders the common login form.
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

# Route that renders the registration form.
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

# Logout route.
@app.route("/logout")
def logout():
    logout_user()
    app.logger.debug("User logged out!")
    return redirect(url_for('home'))

# Route to browse through all sections
@app.route("/sections")
@normal_user_required
def genre():
    sections = Section.query.all()
    return render_template('user_specific/sections.html',sections=sections)

# Route to see a specific section
@app.route("/sections/<name>")
@normal_user_required
def selected_genre(name):
    section = Section.query.filter(Section.name == name.title()).one()
    return render_template('user_specific/genre_list.html',genre = name.title(), books=section.books)

# Route to see user shelf containing all borrowed books.
@app.route("/shelf")
@normal_user_required
def shelf():
    books = [borrow_obj.book for borrow_obj in current_user.borrowed]
    return render_template('user_specific/shelf.html',books=books)

# Route to see a particular book.
@app.route("/book/<id>")
@normal_user_required
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

    return render_template('user_specific/book.html',book=curr_book,
                            avg_score = avg_score, your_score = your_score,
                            num_scores = len(all_ratings), all_authors = all_authors,
                            all_sections = all_sections)

# Stub route to read a particular book.
@app.route("/read/<id>")
@normal_user_required
def read(id):
    return render_template("user_specific/read.html")
    
# Route to see a particular author's details.
@app.route("/author/<id>")
@normal_user_required
def selected_author(id):
    author = Author.query.filter(id == Author.id).one()
    books = author.books
    return render_template('user_specific/author.html',author=author,books=books)

# Route to search for some book.
@app.route("/explore", methods=['GET','POST'])
@normal_user_required
def search():
    form = UserSearchForm()

    if form.validate_on_submit():
        book_name,author_name,section_name = form.book_name.data,form.author_name.data,form.section_name.data
        result = Book.query.filter(Book.name.ilike(f"%{book_name}%"))
        result = result.filter(Book.authors.any(Author.name.ilike(f"%{author_name}%")))
        result = result.filter(Book.sections.any(Section.name.ilike(f"%{section_name}%")))

        result = list(result)
        result.sort()
        return render_template("user_specific/results.html",results = result)

    return render_template("user_specific/explore.html",form = form)

## Librarian routes

# Stub route to see all users and their statuses.
@app.route("/librarian/users")
@librarian_required
def see_users():
    users = User.query.all()
    return render_template("librarian_specific/all_users.html",users = users)

# Route to see all sections.
@app.route("/librarian/sections")
@librarian_required
def see_sections():
    sections = Section.query.all()
    return render_template("librarian_specific/all_sections.html",sections = sections)

# Route to see all books.
@app.route("/librarian/books")
@librarian_required
def see_books():
    books = Book.query.all()
    return render_template("librarian_specific/all_books.html",books = books)

# Route to see all authors.
@app.route("/librarian/authors")
@librarian_required
def see_authors():
    authors = Author.query.all()
    return render_template("librarian_specific/all_authors.html",authors = authors)

# Route to search for some object.
@app.route("/find",methods=['GET','POST'])
@librarian_required
def find_something():
    form = LibrarianSearchForm()

    if form.validate_on_submit():
        if form.obj_type.data == "Book":
            results = Book.query.filter(Book.name.ilike(f"%{form.obj_name.data}%"))
            return render_template("librarian_specific/all_books.html",books = results)

        elif form.obj_type.data == "User":
            results = User.query.filter(User.username.ilike(f"%{form.obj_name.data}%"))
            return render_template("librarian_specific/all_users.html", users = results)
        
        elif form.obj_type.data == "Section":
            results = Section.query.filter(Section.name.ilike(f"%{form.obj_name.data}%"))
            return render_template("librarian_specific/all_sections.html", sections = results)
        
        elif form.obj_type.data == "Author":
            results = Author.query.filter(Author.name.ilike(f"%{form.obj_name.data}%"))
            return render_template("librarian_specific/all_authors.html",authors = results)
        else:
            results = None

        return "Something went wrong",404

    return render_template("librarian_specific/search.html",form = form)

# Route to view a particular book.
@app.route("/librarian/book/<id>")
@librarian_required
def see_specific_book(id):
    book = Book.query.filter(Book.id == id).one()
    return render_template("librarian_specific/object_book.html",book = book)

# Route to view a particular section.
@app.route("/librarian/section/<id>")
@librarian_required
def see_specific_section(id):
    section = Section.query.filter(Section.id == id).one()
    return render_template("librarian_specific/object_section.html",section = section)

# Route to view a particular user.
@app.route("/librarian/user/<id>")
@librarian_required
def see_specific_user(id):
    user = User.query.filter(User.id == id).one()
    return render_template("librarian_specific/object_user.html",user = user)

# Route to view a particular author.
@app.route("/librarian/author/<id>")
@librarian_required
def see_specific_author(id):
    author = Author.query.filter(Author.id == id).one()
    return render_template("librarian_specific/object_author.html",author = author)

# Stub route to edit the details of some user.
@app.route("/librarian/book/edit/<id>",methods = ['GET','POST'])
@librarian_required
def edit_specific_book(id):
    book = Book.query.filter(Book.id == id).one()
    form = EditBookForm()

    if form.validate_on_submit():
        # Logic goes here!
        next = request.args.get('next')
        return redirect(next or url_for('home'))

    return render_template("librarian_specific/edit_book.html",form = form, default = book)

# Stub route to edit the details of some section.
@app.route("/librarian/section/edit/<id>",methods = ['GET','POST'])
@librarian_required
def edit_specific_section(id):
    section = Section.query.filter(Section.id == id).one()
    form = EditSectionForm()

    if form.validate_on_submit():
        # Logic goes here!
        next = request.args.get('next')
        return redirect(next or url_for('home'))

    return render_template("librarian_specific/edit_section.html",form = form, default = section)

# Stub route to edit the details of some author.
@app.route("/librarian/author/edit/<id>",methods = ['GET','POST'])
@librarian_required
def edit_specific_author(id):
    author = Author.query.filter(Author.id == id).one()
    form = EditAuthorForm()

    if form.validate_on_submit():
        # Logic goes here!
        next = request.args.get('next')
        return redirect(next or url_for('home'))

    return render_template("librarian_specific/edit_book.html",form = form, default = author)
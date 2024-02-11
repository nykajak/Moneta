from flask import request,render_template,flash,redirect,url_for
from moneta import app,db,bcrypt,login_manager
from moneta.forms import *
from moneta.models import *
from flask_login import login_user,logout_user,current_user
from functools import wraps

## Utility functions!

# Helper function called internally to login correct user.
@login_manager.user_loader
def load_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    app.logger.info(f"User {user.username} was loaded!")
    return user

# Helper function called internally to display content for pages that do not exist.
@app.errorhandler(404)
def page_not_found(e):
    if not current_user.is_anonymous:
        app.logger.warning(f"The page with url: {request.url} was requested by user: {current_user.username}")
    else:
        app.logger.warning(f"The page with url: {request.url} was requested by an anonymous user")
    return "Page not found",404

# Helper wrapper to ensure that only librarians can access certain pages.
def librarian_required(fun):
    @wraps(fun)
    def inner(*args,**kwargs):
        if not current_user.is_anonymous and current_user.is_librarian:
            return fun(*args,**kwargs)
        else:
            if current_user.is_anonymous:
                app.logger.warning(f"Unauthorised anonymous user tried to access librarian endpoint: {fun.__name__}, {args=}, {kwargs=}")
            else:
                app.logger.warning(f"Unauthorised user ({current_user.username}) tried to access librarian endpoint: {fun.__name__}, {args=}, {kwargs=}")
            return app.login_manager.unauthorized()
    return inner

# Helper wrapper to ensure that only normal users can access certain pages.
def normal_user_required(fun):
    @wraps(fun)
    def inner(*args,**kwargs):
        if not current_user.is_anonymous and not current_user.is_librarian:
            return fun(*args,**kwargs)
        else:
            if current_user.is_anonymous:
                app.logger.warning(f"Unauthorised anonymous user tried to access user endpoint: {fun.__name__}, {args=}, {kwargs=}")
            else:
                app.logger.warning(f"Unauthorised librarian ({current_user.username}) tried to access user endpoint: {fun.__name__}, {args=}, {kwargs=}")
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
            res = login_user(u)
            if res:
                app.logger.info("Successful login!")
            else:
                app.logger.critical("Login failed.")

            next = request.args.get('next')
            return redirect(next or url_for('home'))

        else:
            if not u:
                app.logger.debug(f"No user with email: {form.email.data}!")
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
            app.logger.debug(f"User created with username:{form.username.data}!")
            res = login_user(u)
            if res:
                app.logger.info("User logged in!")
            else:
                app.logger.critical("Login failed.")

            next = request.args.get('next')
            return redirect(next or url_for('home'))
        else:
            pass   

    return render_template("anon_specific/register.html",register_user_form = form)

## Normal user routes.

# Logout route.
@app.route("/logout")
def logout():
    res = logout_user()
    if res:
        app.logger.debug("User logged out!")
    else:
        app.logger.critical("Logout failed.")
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
    section = Section.query.filter(Section.name == name.title()).scalar()
    if not section:
        return render_template('user_specific/non_existant.html')
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
    curr_book = Book.query.filter(Book.id == id).scalar()

    if not curr_book:
        return render_template('user_specific/non_existant.html')
    
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
    author = Author.query.filter(id == Author.id).scalar()
    if not author:
        return render_template('user_specific/non_existant.html')
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
    book = Book.query.filter(Book.id == id).scalar()
    if not book:
        return render_template('librarian_specific/non_existant.html')
    return render_template("librarian_specific/object_book.html",book = book)

# Route to view a particular section.
@app.route("/librarian/section/<id>")
@librarian_required
def see_specific_section(id):
    section = Section.query.filter(Section.id == id).scalar()
    if not section:
        return render_template('librarian_specific/non_existant.html')
    return render_template("librarian_specific/object_section.html",section = section)

# Route to view a particular user.
@app.route("/librarian/user/<id>")
@librarian_required
def see_specific_user(id):
    user = User.query.filter(User.id == id).scalar()
    if not user:
        return render_template('librarian_specific/non_existant.html')
    return render_template("librarian_specific/object_user.html",user = user)

# Route to view a particular author.
@app.route("/librarian/author/<id>")
@librarian_required
def see_specific_author(id):
    author = Author.query.filter(Author.id == id).scalar()
    if not author:
        return render_template('librarian_specific/non_existant.html')
    return render_template("librarian_specific/object_author.html",author = author)

# Stub route to edit the details of some book.
@app.route("/librarian/book/edit/<id>",methods = ['GET','POST'])
@librarian_required
def edit_specific_book(id):
    book = Book.query.filter(Book.id == id).scalar()
    if not book:
        return render_template('librarian_specific/non_existant.html')
    form = EditBookForm()

    if form.validate_on_submit():
        book.name = form.name.data
        book.description = form.description.data
        db.session.commit()

        return redirect(url_for('see_specific_book',id=id))

    return render_template("librarian_specific/edit_book.html",form = form, default = book)

# Stub route to edit the details of some section.
@app.route("/librarian/section/edit/<id>",methods = ['GET','POST'])
@librarian_required
def edit_specific_section(id):
    section = Section.query.filter(Section.id == id).scalar()
    if not section:
        return render_template('librarian_specific/non_existant.html')
    form = EditSectionForm()

    if form.validate_on_submit():
        section.name = form.name.data
        section.description = form.description.data
        db.session.commit()

        return redirect(url_for('see_specific_section',id=id))

    return render_template("librarian_specific/edit_section.html",form = form, default = section)

# Stub route to edit the details of some author.
@app.route("/librarian/author/edit/<id>",methods = ['GET','POST'])
@librarian_required
def edit_specific_author(id):
    author = Author.query.filter(Author.id == id).scalar()
    if not author:
        return render_template('librarian_specific/non_existant.html')
    form = EditAuthorForm()

    if form.validate_on_submit():
        author.name = form.name.data
        author.bio = form.description.data
        db.session.commit()

        return redirect(url_for('see_specific_author',id=id))

    return render_template("librarian_specific/edit_author.html",form = form, default = author)

# Route to delete specific user.
@app.route("/librarian/user/delete/<id>")
@librarian_required
def delete_specific_user(id):   
     
    obj = User.query.filter(User.id == id).scalar()
    if not obj:
        return render_template('librarian_specific/non_existant.html')
    
    db.session.query(Borrow).filter(Borrow.user_id == id).delete()
    db.session.query(Return).filter(Return.user_id == id).delete()
    db.session.query(Comment).filter(Comment.user_id == id).delete()
    db.session.query(Rating).filter(Rating.user_id == id).delete()

    db.session.delete(obj)
    db.session.commit()
    return redirect(url_for('see_users'))

# Route to delete specific book.
@app.route("/librarian/book/delete/<id>")
@librarian_required
def delete_specific_book(id):  
    
    obj = Book.query.filter(Book.id == id).scalar()
    if not obj:
        return render_template('librarian_specific/non_existant.html')

    db.session.query(written).filter(written.c.book_id == id).delete()
    db.session.query(category).filter(category.c.book_id == id).delete()
    db.session.query(Borrow).filter(Borrow.book_id == id).delete()
    db.session.query(Comment).filter(Comment.book_id == id).delete()
    db.session.query(Rating).filter(Rating.book_id == id).delete()

    db.session.delete(obj)
    db.session.commit()  
    return redirect(url_for('see_books'))

@app.route("/librarian/section/delete/<id>")
@librarian_required
def delete_specific_section(id): 
    
    obj = Section.query.filter(Section.id == id).scalar()
    if not obj:
        return render_template('librarian_specific/non_existant.html')
    
    db.session.query(category).filter(category.c.section_id == id).delete()

    db.session.delete(obj)
    db.session.commit()   
    return redirect(url_for('see_sections'))

@app.route("/librarian/author/delete/<id>")
@librarian_required
def delete_specific_author(id):
    
    obj = Author.query.filter(Author.id == id).scalar()
    if not obj:
        return render_template('librarian_specific/non_existant.html')
    
    db.session.query(written).filter(written.c.author_id == id).delete()

    db.session.delete(obj)
    db.session.commit() 
    return redirect(url_for('see_authors'))

@app.route("/librarian/confirm/<message><id>")
@librarian_required
def confirm_action(message,id):
    print(id)
    action = {"message":message}
    if "User" in message:
        action["route"] = url_for('see_users')
    elif "Author" in message:
        action["route"] = url_for('see_authors')
    elif "Book" in message:
        action["route"] = url_for('see_books')
    else:
        action["route"] = url_for('see_sections')
    return render_template("librarian_specific/confirm.html",action=action)
# Imports
from flask import request,render_template,flash,redirect,url_for
from api import app,db,bcrypt,login_manager
from api.forms import *
from api.models import *
from flask_login import login_user,logout_user,current_user
from functools import wraps
from sqlalchemy import insert,func
from datetime import timedelta,datetime

## Utility functions!

# Helper function called internally to login correct user.
# Tested OK - Gamma
@login_manager.user_loader
def load_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    return user

# Helper function called internally to display content for pages that do not exist.
# Tested OK - Gamma
@app.errorhandler(404)
def page_not_found(e):
    return "Page not found",404

# Helper wrapper to ensure that only librarians can access certain pages.
# Tested OK - Gamma
def librarian_required(fun):
    @wraps(fun)
    def inner(*args,**kwargs):
        if not current_user.is_anonymous and current_user.is_librarian:
            return fun(*args,**kwargs)
        else:
            return app.login_manager.unauthorized()
    return inner

# Helper wrapper to ensure that only normal users can access certain pages.
# Tested OK - Gamma
def normal_user_required(fun):
    @wraps(fun)
    def inner(*args,**kwargs):
        if not current_user.is_anonymous and not current_user.is_librarian:
            return fun(*args,**kwargs)
        else:
            return app.login_manager.unauthorized()
    return inner    

# Route that reroutes user to their profile page if logged in, the about page if not.
# Tested OK - Gamma
@app.route("/")
def home():
    return render_template("base_templates/home.html")

## Global user routes

# Route that renders the common login form
# Tested OK - Gamma
@app.route("/login",methods=['GET','POST'])
def login():
    form = MyLoginForm()

    if form.validate_on_submit():
        
        u = User.query.filter_by(email=form.email.data).first()

        if u and bcrypt.check_password_hash(u.password,form.password.data):
            res = login_user(u)

            # Remove expired books from user on login
            for b in current_user.borrowed:
                if (datetime.now() - b.b_date).days > 7:
                    obj = b
                    try:
                        db.session.add(Read(user_id = obj.user_id, book_id = obj.book_id))
                        db.session.commit()
                    except Exception:
                        db.session.rollback()
                    
                    Borrow.query.filter(Borrow.user_id == obj.user_id).filter(Borrow.book_id == obj.book_id).delete()
                    db.session.commit()

            return redirect(url_for('home'))

        else:
            if not u:
                flash("No such user found!",category="danger")
            else:
                flash("Incorrect password!",category="danger")

    return render_template("anon_specific/login.html",login_user_form = form)

# Route that renders the registration form.
# Tested OK- Gamma
@app.route("/register",methods=['GET','POST'])
def register():
    form = MyRegistrationForm()

    if form.validate_on_submit():

        hashed_password = bcrypt.generate_password_hash(form.password.data)
        u = User(username=form.username.data,email=form.email.data,password=hashed_password)
        created = 0
        try:
            #Creating user.
            db.session.add(u)
            db.session.commit()
            created = 1

        except Exception as E:
            #Detecting which field repeated via the error message.
            failed = E.args[0][56:]
            if failed == 'email':
                flash("Email already in use",category='danger')
            elif failed == 'username':
                flash("Username already in use",category='danger')
                

        if created:
            res = login_user(u)

            return redirect(url_for('home'))

    return render_template("anon_specific/register.html",register_user_form = form)

# Logout route.
# Tested OK- Gamma
@app.route("/logout")
def logout():
    curr_name = current_user.username
    res = logout_user()
    return redirect(url_for('home'))

## Normal user routes.

# Route to browse through all available sections.
# Tested OK- Gamma
@app.route("/sections")
@normal_user_required
def genre():
    sections = Section.query.all()
    return render_template('user_specific/sections.html',sections=sections)

# Route to see a specific section by name.
# Tested OK - Gamma
@app.route("/sections/<name>")
@normal_user_required
def selected_genre(name):
    section = Section.query.filter(func.lower(Section.name) == name.lower()).scalar()
    if not section:
        return render_template('user_specific/non_existant.html')
    return render_template('user_specific/specific_section.html',genre = section)

# Route to see recently added and highly rated books.
# Tested OK - Gamma
@app.route("/trending")
@normal_user_required
def trending():
    all_books = Book.query.order_by(Book.id).all()

    # Get last added five books with most recent book first.
    new_books = all_books[-5::]
    new_books = new_books[::-1]
    
    # Get top N books.
    N = 5
    top_books = []
    for book in all_books:
        top_books.append((book.get_rating(),book))
        if len(top_books) > N:
            top_books.sort(reverse=True)
            top_books.pop()

    return render_template('user_specific/trending.html', new_books = new_books,top_books = top_books)

# Route to see a particular book.
# Tested OK - Gamma
@app.route("/book/<id>")
@normal_user_required
def selected_book(id):
    curr_book = Book.query.filter(Book.id == id).scalar()

    if not curr_book:
        return render_template('user_specific/non_existant.html')
    
    # Info related to rating and number of ratings
    num_ratings = len(list(curr_book.ratings))
    avg_score = curr_book.get_rating()
    your_score = Rating.query.filter(Rating.book_id == curr_book.id).filter(Rating.user_id == current_user.id).scalar()
    if your_score:
        your_score = your_score.score

    # State value and what it means:
    # 3: Can be requested
    # 2: Insufficient space / Awaiting return
    # 1: Already requested
    # 0: Already borrowed
    state = 3

    if len(current_user.borrowed) + len(current_user.requested) + len(current_user.returned) >= 5:
        state = 2

    # Check if currently borrowed.
    return_date = None
    for b in current_user.borrowed:
        if b.book.name == curr_book.name:
            state = 0
            return_date = b.b_date + timedelta(days=7)
            return_date = return_date.__str__()
            return_date = return_date[:10:]
            break
    
    # Check if currently requested.
    for b in current_user.requested:
        if b.book.name == curr_book.name:
            state = 1
            break

    # Check if currently returned and awaiting processing.
    for b in current_user.returned:
        if b.book.name == curr_book.name:
            state = 2
            break

    return render_template('user_specific/book.html',book=curr_book,
                            avg_score = avg_score, your_score = your_score,
                            state = state, return_date=return_date, num_ratings = num_ratings)

# Route to read a particular book.
# Tested OK - Gamma
@app.route("/read",methods = ["POST"])
@normal_user_required
def read():
    book_id = request.form.get("book_id")
    
    # Sanity check for book being actually borrowed.
    owned = 0
    for b in current_user.borrowed:
        if b.book.id == int(book_id):
            owned = 1
            break

    if not owned:
        return app.login_manager.unauthorized()
    
    book = Book.query.filter(Book.id == book_id).scalar()
    if not book:
        return render_template('user_specific/non_existant.html')
    
    src = Content.query.filter(Content.book_id == book_id).scalar()
    if src:
        src = src.filename
    else:
        return render_template('user_specific/non_existant.html')

    return redirect(src)

#Route to request a particular book
# Tested OK - Gamma
@app.route("/request",methods = ["POST"])
@normal_user_required
def request_book():
    book_id = request.form.get("book_id")
    user_id = current_user.id

    # Sanity check in case of POST request being sent
    if len(current_user.requested) + len(current_user.borrowed) + len(current_user.returned) >= 5:
        return app.login_manager.unauthorized()

    # Adding the request object. Checking for duplicates just in case.
    try:
        b = Requested(book_id = book_id, user_id = user_id)
        db.session.add(b)
        db.session.commit()
    except:
        db.session.rollback()

    return redirect(url_for("home"))

#Route to cancel request of a particular book
# Tested OK - Gamma
@app.route("/request/cancel",methods = ["POST"])
@normal_user_required
def cancel_request_book():
    book_id = request.form.get("book_id")
    user_id = current_user.id

    # Deleting request object. No try catch here.
    Requested.query.filter(Requested.book_id == book_id).filter(Requested.user_id == user_id).delete()
    db.session.commit()
    return redirect(url_for("home"))

#Route to return a particular book
# Tested OK - Gamma
@app.route("/return",methods = ["POST"])
@normal_user_required
def _return():
    book_id = request.form.get("book_id")
    user_id = current_user.id

    query = Borrow.query.filter(Borrow.book_id == book_id).filter(Borrow.user_id == user_id)
    record = query.scalar()
    
    if not Return.query.filter(Return.book_id == record.book_id).filter(Return.user_id == record.user_id).scalar():
        try:
            # Adding Return object.
            return_obj = Return(book_id = record.book_id, user_id = record.user_id, b_date = record.b_date)
            db.session.add(return_obj)
            db.session.commit()
        except:
            db.session.rollback()

    # Removing Borrow object.
    query.delete()
    db.session.commit()

    return redirect(url_for("home"))

#Route to rate a particular book
# Tested OK - Gamma
@app.route("/rate",methods = ["POST"])
@normal_user_required
def rate():
    book_id = request.form.get("book_id")
    score = request.form.get("score")
    user_id = current_user.id

    # Checking if record exists and overwriting as necessary.
    record = Rating.query.filter(Rating.book_id == book_id).filter(Rating.user_id == user_id).scalar()
    if record:
        record.score = score
    else:
        db.session.add(Rating(book_id = book_id, user_id = user_id, score = score))
    db.session.commit()

    return redirect(url_for("selected_book",id=book_id))

#Route to comment on a particular book
# Tested OK - Gamma
@app.route("/comment",methods = ["POST"])
@normal_user_required
def comment():
    book_id = request.form.get("book_id")
    content = request.form.get("content")
    user_id = current_user.id

    # Computing id of new comment.
    highest_id = db.session.query(func.max(Comment.id)).scalar()
    if not highest_id:
        highest_id = 1

    # Adding Comment object.
    obj = Comment(id = highest_id + 1, book_id = book_id, user_id = user_id, content = content)
    db.session.add(obj)
    db.session.commit()

    return redirect(url_for("selected_book",id=book_id))

# Route to remove a comment on book for user.
# Tested OK - Gamma
@app.route("/comment/remove/book/<id>")
@normal_user_required
def remove_own_comment(id):
    comment = Comment.query.filter(Comment.id == id)
    obj = comment.scalar()
    redirect_id = obj.book_id

    # Sanity check: Is it own comment?
    if obj.user_id == current_user.id:
        comment.delete()
        db.session.commit()

        return redirect(url_for("selected_book",id = redirect_id))
    
    return app.login_manager.unauthorized()
    
# Route to see a particular author's details.
# Tested OK - Gamma
@app.route("/author/<id>")
@normal_user_required
def selected_author(id):
    author = Author.query.filter(id == Author.id).scalar()
    if not author:
        return render_template('user_specific/non_existant.html')
    return render_template('user_specific/author.html',author=author)

# Route to search for some book.
# Tested OK - Gamma
@app.route("/explore", methods=['GET','POST'])
@normal_user_required
def search():
    form = UserSearchForm()

    if form.validate_on_submit():
        book_name,author_name,section_name = form.book_name.data,form.author_name.data,form.section_name.data
        
        # Applying Criteria
        result = Book.query.filter(Book.name.ilike(f"%{book_name}%"))
        result = result.filter(Book.authors.any(Author.name.ilike(f"%{author_name}%")))
        result = result.filter(Book.sections.any(name=section_name))

        result = result.order_by(Book.name).all()
        if result:
            return render_template("user_specific/results.html",results = result)
        else:
            return render_template("user_specific/non_existant.html")

    return render_template("user_specific/explore.html",form = form)

## Librarian routes

# Main navigation page for librarians to view all objects.
# Tested OK - Gamma
@app.route("/librarian/browse")
@librarian_required
def browse():
    return render_template("librarian_specific/browse.html")

# Route to see all users.
# Tested OK - Gamma
@app.route("/librarian/users")
@librarian_required
def see_users():
    users = User.query.order_by(User.username).all()
    # Jinja2 handles not displaying librarian users.
    return render_template("librarian_specific/all_users.html",users = users)

# Route to see all sections.
# Tested OK - Gamma
@app.route("/librarian/sections")
@librarian_required
def see_sections():
    sections = Section.query.order_by(Section.name).all()
    return render_template("librarian_specific/all_sections.html",sections = sections)

# Route to see all books.
# Tested OK - Gamma
@app.route("/librarian/books")
@librarian_required
def see_books():
    books = Book.query.order_by(Book.name).all()
    return render_template("librarian_specific/all_books.html",books = books)

# Route to see all authors.
# Tested OK - Gamma
@app.route("/librarian/authors")
@librarian_required
def see_authors():
    authors = Author.query.all()
    return render_template("librarian_specific/all_authors.html",authors = authors)

# Route to see all requests.
# Tested OK - Gamma
@app.route("/librarian/requests")
@librarian_required
def see_requests():
    requests = Requested.query.all()
    returned = Return.query.all()
    return render_template("librarian_specific/all_requests.html",requests = requests, returned = returned)

# Route to handle a return requests.
# Tested OK - Gamma
@app.route("/librarian/return/handle/<id>")
@librarian_required
def handled_return(id):
    res = Return.query.filter(Return.id == id)
    obj = res.scalar()
    if not obj:
        return render_template('librarian_specific/non_existant.html')
    
    try:
        # Adding the Read object
        db.session.add(Read(user_id=obj.user_id,book_id=obj.book_id))
        db.session.commit()

    except Exception as E:
        db.session.rollback()

    # Deleting the Return object
    res.delete()
    db.session.commit()

    return redirect(url_for('see_requests'))

# Route to search for some object.
# Tested OK - Gamma
@app.route("/find",methods=['GET','POST'])
@librarian_required
def find_something():
    form = LibrarianSearchForm()

    if form.validate_on_submit():
        if form.obj_type.data == "Book":
            results = Book.query.filter(Book.name.ilike(f"%{form.obj_name.data}%")).order_by(Book.name).all()
            return render_template("librarian_specific/all_books.html",books = results)

        elif form.obj_type.data == "User":
            results = User.query.filter(User.username.ilike(f"%{form.obj_name.data}%")).order_by(User.username).all()
            return render_template("librarian_specific/all_users.html", users = results)
        
        elif form.obj_type.data == "Section":
            results = Section.query.filter(Section.name.ilike(f"%{form.obj_name.data}%")).order_by(Section.name).all()
            return render_template("librarian_specific/all_sections.html", sections = results)
        
        elif form.obj_type.data == "Author":
            results = Author.query.filter(Author.name.ilike(f"%{form.obj_name.data}%")).order_by(Author.name).all()
            return render_template("librarian_specific/all_authors.html",authors = results)
        else:
            results = None

        return render_template("librarian_specific/non_existant.html")

    return render_template("librarian_specific/search.html",form = form)

# Route to view a particular book.
# Tested OK - Gamma
@app.route("/librarian/book/<id>")
@librarian_required
def see_specific_book(id):
    book = Book.query.filter(Book.id == id).scalar()
    if not book:
        return render_template('librarian_specific/non_existant.html')
    return render_template("librarian_specific/object_book.html",book = book)

# Route to view a particular section.
# Tested OK - Gamma
@app.route("/librarian/section/<id>")
@librarian_required
def see_specific_section(id):
    section = Section.query.filter(Section.id == id).scalar()
    if not section:
        return render_template('librarian_specific/non_existant.html')
    return render_template("librarian_specific/object_section.html",section = section)

# Route to view a particular user.
# Tested OK - Gamma
@app.route("/librarian/user/<id>")
@librarian_required
def see_specific_user(id):
    user = User.query.filter(User.id == id).scalar()

    # Librarians cannot interfere with each other.
    if user.is_librarian:
        return app.login_manager.unauthorized()

    if not user:
        return render_template('librarian_specific/non_existant.html')
    return render_template("librarian_specific/object_user.html",user = user)

# Route to view a particular author.
# Tested OK - Gamma
@app.route("/librarian/author/<id>")
@librarian_required
def see_specific_author(id):
    author = Author.query.filter(Author.id == id).scalar()
    if not author:
        return render_template('librarian_specific/non_existant.html')
    return render_template("librarian_specific/object_author.html",author = author)

# Route to edit the details of some book.
# Tested OK - Gamma
@app.route("/librarian/book/edit/<id>",methods = ['GET','POST'])
@librarian_required
def edit_specific_book(id):
    book = Book.query.filter(Book.id == id).scalar()
    if not book:
        return render_template('librarian_specific/non_existant.html')

    form = EditBookForm()

    obj = Content.query.filter(Content.book_id == id).scalar()
    default_path = obj.filename

    if form.validate_on_submit():
        # Update attrs.
        book.name = form.name.data
        if form.description.data != "None":
            book.description = form.description.data
        else:
            book.description = None
        new_path = form.file_path.data

        # Update content.
        content_obj = Content.query.filter(Content.book_id == id).scalar()
        content_obj.filename = new_path
        db.session.commit()

        return redirect(url_for('see_specific_book',id=id))

    return render_template("librarian_specific/edit_book.html",form = form, default = book, default_path = default_path)

# Route to edit the details of some section.
# Tested OK - Gamma
@app.route("/librarian/section/edit/<id>",methods = ['GET','POST'])
@librarian_required
def edit_specific_section(id):
    section = Section.query.filter(Section.id == id).scalar()
    if not section:
        return render_template('librarian_specific/non_existant.html')
    form = EditSectionForm()

    if form.validate_on_submit():
        section.name = form.name.data
        if form.description.data != "None":
            section.description = form.description.data
        else:
            section.description = None
        db.session.commit()

        return redirect(url_for('see_specific_section',id=id))

    return render_template("librarian_specific/edit_section.html",form = form, default = section)

# Stub route to edit the details of some author.
# Tested OK - Gamma
@app.route("/librarian/author/edit/<id>",methods = ['GET','POST'])
@librarian_required
def edit_specific_author(id):
    author = Author.query.filter(Author.id == id).scalar()
    if not author:
        return render_template('librarian_specific/non_existant.html')
    form = EditAuthorForm()

    if form.validate_on_submit():
        author.name = form.name.data
        if form.description.data != "None":
            author.bio = form.description.data
        else:
            author.bio = None
        db.session.commit()

        return redirect(url_for('see_specific_author',id=id))

    return render_template("librarian_specific/edit_author.html",form = form, default = author)

# Route to delete specific user.
# Tested OK - Gamma
@app.route("/librarian/user/delete/<id>")
@librarian_required
def delete_specific_user(id):   
     
    obj = User.query.filter(User.id == id).scalar()
    if not obj:
        return render_template('librarian_specific/non_existant.html')
    
    # Everything to be deleted
    db.session.query(Borrow).filter(Borrow.user_id == id).delete()
    db.session.query(Read).filter(Read.user_id == id).delete()
    db.session.query(Return).filter(Return.user_id == id).delete()
    db.session.query(Requested).filter(Requested.user_id == id).delete()
    db.session.query(Comment).filter(Comment.user_id == id).delete()
    db.session.query(Rating).filter(Rating.user_id == id).delete()

    db.session.delete(obj)
    db.session.commit()
    return redirect(url_for('see_users'))

# Route to delete specific book.
# Tested OK - Gamma
@app.route("/librarian/book/delete/<id>")
@librarian_required
def delete_specific_book(id):  
    
    obj = Book.query.filter(Book.id == id).scalar()
    if not obj:
        return render_template('librarian_specific/non_existant.html')

    # Everything to be deleted
    db.session.query(written).filter(written.c.book_id == id).delete()
    db.session.query(category).filter(category.c.book_id == id).delete()
    db.session.query(Requested).filter(Requested.book_id == id).delete()
    db.session.query(Read).filter(Read.book_id == id).delete()
    db.session.query(Return).filter(Return.book_id == id).delete()
    db.session.query(Borrow).filter(Borrow.book_id == id).delete()
    db.session.query(Comment).filter(Comment.book_id == id).delete()
    db.session.query(Content).filter(Content.book_id == id).delete()
    db.session.query(Rating).filter(Rating.book_id == id).delete()

    db.session.delete(obj)
    db.session.commit()  
    return redirect(url_for('see_books'))

# Route to delete specific section.
# Tested OK - Gamma
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

# Route to delete specific author.
# Tested OK - Gamma
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

# Route to remove author from a book.
# Tested OK - Gamma
@app.route("/librarian/author/remove/book",methods=['POST'])
@librarian_required
def remove_book_from_author():
    author_id,book_id = request.form.get("author_id"),request.form.get("book_id")
    db.session.query(written).filter(written.c.book_id == book_id).filter(written.c.author_id == author_id).delete()
    db.session.commit()

    # Rerouting
    origin = request.form.get("origin")
    if origin:
        return redirect(url_for("see_specific_author",id = author_id))
    else:
        return redirect(url_for("see_specific_book",id = book_id))

# Route to remove section from a book.
# Tested OK - Gamma
@app.route("/librarian/section/remove/book",methods=['POST'])
@librarian_required
def remove_book_from_section():
    section_id,book_id = request.form.get("section_id"),request.form.get("book_id")
    db.session.query(category).filter(category.c.book_id == book_id).filter(category.c.section_id == section_id).delete()
    db.session.commit()

    # Rerouting
    origin = request.form.get("origin")
    if origin:
        return redirect(url_for("see_specific_section",id = section_id))
    else:
        return redirect(url_for("see_specific_book",id = book_id))

# Route to remove a book from a user.
# Tested OK - Gamma
@app.route("/librarian/user/remove/book",methods=['POST'])
@librarian_required
def remove_book_from_user():
    user_id,book_id = request.form.get("user_id"),request.form.get("book_id")

    # Removing Borrow object
    db.session.query(Borrow).filter(Borrow.book_id == book_id).filter(Borrow.user_id == user_id).delete()
    db.session.commit()

    # Adding Read object
    try:
        db.session.add(Read(user_id = user_id, book_id = book_id))
        db.session.commit()
    except:
        db.session.rollback()

    # Rerouting
    origin = request.form.get("origin")
    if origin:
        return redirect(url_for("see_specific_user",id = user_id))
    else:
        return redirect(url_for("see_specific_book",id = book_id))
    
# Route to remove a comment on book from a user.
# Tested OK - Gamma
@app.route("/librarian/comment/remove/book/<id>")
@librarian_required
def remove_comment_from_book(id):
    comment = Comment.query.filter(Comment.id == id)
    id_redirect = comment.scalar().book_id
    comment.delete()
    db.session.commit()

    return redirect(url_for("see_specific_book",id=id_redirect))

# Route to add an author to a book.
# Tested OK - Gamma
@app.route("/librarian/author/include",methods=['POST'])
@librarian_required
def add_author_to_book():    
    if "author_name" in request.form.keys():
        author_name = request.form.get("author_name")
        book_id = request.form.get("book_id")

        author = Author.query.filter(Author.name == author_name).scalar()
        if not author:
            return render_template('librarian_specific/non_existant.html')
        
        present = db.session.query(written).filter(written.c.book_id == book_id).filter(written.c.author_id == author.id).scalar()
        if not present:
            stmt =(
                insert(written).
                values(book_id=book_id,author_id=author.id)
            )

            db.session.execute(stmt)
            db.session.commit()
        else:
            return "Duplicates not allowed"
        
        return redirect(url_for('see_specific_book',id=book_id))
    
    else:
        author_id = request.form.get("author_id")
        book_name = request.form.get("book_name")
        
        book = Book.query.filter(Book.name == book_name).scalar()
        if not book:
            return render_template('librarian_specific/non_existant.html')
        
        present = db.session.query(written).filter(written.c.book_id == book.id).filter(written.c.author_id == author_id).scalar()
        if not present:
            stmt =(
                insert(written).
                values(book_id=book.id,author_id=author_id)
            )

            db.session.execute(stmt)
            db.session.commit()
        else:
            return "Duplicates not allowed"

        return redirect(url_for('see_specific_author',id=author_id))

# Route to add a section to a book.
# Tested OK - Gamma
@app.route("/librarian/section/include",methods=['POST'])
@librarian_required
def add_section_to_book():
    if "section_name" in request.form.keys():
        section_name = request.form.get("section_name")
        book_id = request.form.get("book_id")

        section = Section.query.filter(Section.name == section_name).scalar()
        if not section:
            return render_template('librarian_specific/non_existant.html')
        
        present = db.session.query(category).filter(category.c.book_id == book_id).filter(category.c.section_id == section.id).scalar()
        if not present:
            stmt =(
                insert(category).
                values(book_id=book_id,section_id=section.id)
            )

            db.session.execute(stmt)
            db.session.commit()
        else:
            return "Duplicates not allowed"

        return redirect(url_for('see_specific_book',id=book_id))
    
    else:
        section_id = request.form.get("section_id")
        book_name = request.form.get("book_name")

        book = Book.query.filter(Book.name == book_name).scalar()
        if not book:
            return render_template('librarian_specific/non_existant.html')
        
        present = db.session.query(category).filter(category.c.book_id == book.id).filter(category.c.section_id == section_id).scalar()
        if not present:
            stmt =(
                insert(category).
                values(book_id=book.id,section_id=section_id)
            )

            db.session.execute(stmt)
            db.session.commit()
        else:
            return "Duplicates not allowed"

        return redirect(url_for('see_specific_section',id=section_id))

# Route to add some item - be it author, class or book with default values except for names.
# Tested OK - Gamma
@app.route("/librarian/item/add",methods=['POST'])
@librarian_required
def add_item():
    kind = request.form.get("kind")
    data = request.form.get("user_input")

    if kind == "author":
        cls = Author
    elif kind == "book":
        cls = Book
    elif kind == "section":
        cls = Section

    obj = cls(name=data)

    try:
        db.session.add(obj)
        db.session.commit()

    except:
        db.session.rollback()
        return "Duplicates not allowed!"
    
    if kind == "book":
        try:
            db.session.add(Content(book_id = obj.id, filename = "https://drive.google.com/file/d/1a7k6giBy_fBfbH2GwxytDLjnLcVfN5GF/view?usp=sharing"))
            db.session.commit()
        except:
            db.session.rollback()
    
    if kind == "author":
        return redirect(url_for('see_authors'))
    elif kind == "book":
        return redirect(url_for('see_books'))
    else:
        return redirect(url_for('see_sections'))
    
#Route to grant a particular request
# Tested OK - Gamma
@app.route("/librarian/grant/<id>")
@librarian_required
def grant(id):
    query = Requested.query.filter(Requested.id == id)
    obj = query.scalar()

    book_id = obj.book_id
    user_id = obj.user_id

    b = Borrow(book_id = book_id, user_id = user_id)
    db.session.add(b)

    query.delete()
    db.session.commit()
    return redirect(url_for("see_requests"))

#Route to reject a particular request
# Tested OK - Gamma
@app.route("/librarian/reject/<id>")
@librarian_required
def reject(id):
    query = Requested.query.filter(Requested.id == id)
    query.delete()
    db.session.commit()
    return redirect(url_for("see_requests"))
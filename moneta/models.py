# Imports
from moneta.database import db 
from datetime import date
from flask_login import UserMixin

# Leftovers from previous attempts
# from flask_security import UserMixin,RoleMixin
# from flask_security.models import fsqla_v3 as fsqla

# Table to store written relation between Book and Author
written = db.Table('written',
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
    db.Column('author_id', db.Integer, db.ForeignKey('author.id'), primary_key=True)
)

# Table to store category relation between Book and Section
category = db.Table('category',
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
    db.Column('section_id', db.Integer, db.ForeignKey('section.id'), primary_key=True)
)

class Content(db.Model):
    """
        Class that maps books to filenames.
    """
    __tablename__ = "content"

    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), primary_key=True)
    filename = db.Column(db.Text, nullable=False)

class User(db.Model,UserMixin):
    """
        Representative class for a user. Has a boolean denoting whether user is a librarian
        or not.
    """
    __tablename__ = "user"

    # Fields
    id = db.Column(db.Integer,primary_key = True)
    username = db.Column(db.String(20),nullable=False,unique=True)
    password = db.Column(db.String(60),nullable=True)
    email = db.Column(db.String(60),nullable=False,unique=True)
    doj = db.Column(db.DateTime, nullable=False, default = date.today())
    is_librarian = db.Column(db.Integer,nullable = False, default = 0)

    # Remnants of a previous system.
    # is_active = db.Column(db.Boolean(),nullable=False,default=1)
    # is_authenticated = db.Column(db.Boolean(),nullable=False)
    # is_anonymous = db.Column(db.Boolean(),nullable=False,default=0)

    # Reference to all the borrow objects corresponding to books currently borrowed
    borrowed = db.relationship('Borrow',backref='user',lazy=True)

    # Reference to all the return objects corresponding to books already returned
    returned = db.relationship('Return',backref='user',lazy=True)

    # Reference to all the comments made by user
    comments = db.relationship('Comment',backref = 'user', lazy=True)

    # Reference to all the request made by user
    requested = db.relationship('Requested',backref = 'user', lazy=True)

    def __repr__(self):
        return f"User({self.username},{self.email})"
    
    # Remnants of a previous system.
    # def get_id(self):
    #     return str(self.id)

class Book(db.Model):
    """
        Representative class for a book.
    """
    __tablename__ = "book"

    # Fields
    id = db.Column(db.Integer,primary_key = True)
    name = db.Column(db.String(80), unique = True, nullable = False)
    description = db.Column(db.Text)

    # Reference to all ratings assigned to the book
    ratings = db.relationship('Rating',backref='book',lazy=True)

    # Reference to all comments associated with the book
    comments = db.relationship('Comment',backref = 'book', lazy=True)

    #Reference to all borrow objects
    borrowed = db.relationship('Borrow',backref = 'book',lazy=True)

    #Reference to all request objects
    requested = db.relationship('Requested',backref = 'book',lazy=True)

    def __repr__(self):
        return f'Book({self.name})'
    

    def __lt__(self,other):
        return self.name < other.name
    
class Author(db.Model):
    """
        Representative class for an author.
    """
    __tablename__ = 'author'

    #Fields
    id = db.Column(db.Integer,primary_key = True)
    name = db.Column(db.String(80), unique = True, nullable = False)
    bio = db.Column(db.Text)

    # Reference to all ratings written by author and vice versa.
    books = db.relationship('Book',secondary=written,backref = db.backref('authors',lazy='dynamic') )

    def __repr__(self):
        return f'Author({self.name})'

class Section(db.Model):
    """
        Representative class for an author.
    """
    __tablename__ = "section"

    # Fields
    id = db.Column(db.Integer,primary_key = True)
    name = db.Column(db.String(40), unique = True, nullable = False)
    doc = db.Column(db.DateTime, default = date.today())
    description = db.Column(db.String(256))

    # Reference to all books in section and book.sections to find all sections book belongs to.
    books = db.relationship('Book',secondary=category,backref = db.backref('sections',lazy='dynamic') )

    def __repr__(self):
        return f"Section({self.name}, {self.description})"
    

class Comment(db.Model):
    """
        Representative class for a comment.
    """
    __tablename__ = "comment"

    user_id = db.Column(db.Integer,db.ForeignKey("user.id"),primary_key=True)
    book_id = db.Column(db.Integer,db.ForeignKey("book.id"),primary_key=True)
    content = db.Column(db.Text,nullable=False)
    id = db.Column(db.Integer,primary_key = True)

    def __repr__(self):
        return f"Comment({self.user_id},{self.book_id})"
    
class Rating(db.Model):
    """
        Representative class for some rating associated with the book.
    """
    __tablename__ = "rating"

    book_id = db.Column(db.Integer,db.ForeignKey("book.id"),primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey("user.id"),primary_key=True)
    score = db.Column(db.Integer, nullable = False)

    def __repr__(self):
        return f"Rating({self.user_id},{self.book_id})"

class Borrow(db.Model):
    """
        Representative class for the borrow relation between a book and a user.
    """
    __tablename__ = "borrow"

    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    b_date = db.Column(db.DateTime, nullable = False, default = date.today())

    # book = db.relationship('Book',lazy= True)

    def __repr__(self):
        return f"Borrow({self.user_id},{self.book_id},{self.b_date})"
    
class Return(db.Model):
    """
        Representative class for the returned relation between a book and a user.
    """
    __tablename__ = "return"

    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    b_date = db.Column(db.DateTime, nullable = False)
    r_date = db.Column(db.DateTime, nullable = False, default = date.today())

    book = db.relationship('Book',lazy= True)

    def __repr__(self):
        return f"Return({self.user_id},{self.book_id},{self.r_date})"
    
class Requested(db.Model):
    """
        Representative class for the requested relation between a book and a user.
    """
    __tablename__ = "requested"

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    r_date = db.Column(db.DateTime, nullable = False, default = date.today())

    # book = db.relationship('Book',lazy= True)

    def __repr__(self):
        return f"Requested({self.user_id},{self.book_id},{self.r_date})"
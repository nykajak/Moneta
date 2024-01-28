from moneta.database import db 
from datetime import date
from flask_login import UserMixin
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

# Table to keep track of roles between User and Role
permission = db.Table('permission',
    db.Column('user_id',db.Integer,db.ForeignKey("user.id"),primary_key=True),
    db.Column('role_id',db.Integer,db.ForeignKey("role.id"),primary_key=True)
)

class User(db.Model,UserMixin):
    __tablename__ = "user"

    # Fields
    id = db.Column(db.Integer,primary_key = True)
    username = db.Column(db.String(20),nullable=False,unique=True)
    password = db.Column(db.String(60),nullable=True)
    email = db.Column(db.String(60),nullable=False,unique=True)
    doj = db.Column(db.DateTime, nullable=False, default = date.today())
    # is_active = db.Column(db.Boolean(),nullable=False,default=1)
    # is_authenticated = db.Column(db.Boolean(),nullable=False)
    # is_anonymous = db.Column(db.Boolean(),nullable=False,default=0)

    # Reference to all the borrow objects corresponding to books currently borrowed
    borrowed = db.relationship('Borrow',backref='user',lazy=True)

    # Reference to all roles assigned to the user
    roles = db.relationship('Role',secondary=permission,backref = db.backref('users',lazy='dynamic'))

    def __repr__(self):
        return f"User({self.username},{self.email})"
    
    # def get_id(self):
    #     return str(self.id)

class Role(db.Model):
    __tablename__ = "role"

    # Fields
    id = db.Column(db.Integer,primary_key = True)
    name = db.Column(db.String(20),nullable = False)
    description = db.Column(db.String(256))

class Book(db.Model):
    __tablename__ = "book"

    # Fields
    id = db.Column(db.Integer,primary_key = True)
    name = db.Column(db.String(80), unique = True, nullable = False)
    description = db.Column(db.Text)

    # Reference to all ratings assigned to the book
    ratings = db.relationship('Rating',backref='book',lazy=True)

    # Reference to all comments associated with the book
    comments = db.relationship('Comment',backref = 'book', lazy=True)

    def __repr__(self):
        return f'Book({self.name})'
    
class Author(db.Model):
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
    __tablename__ = "comment"

    user_id = db.Column(db.Integer,db.ForeignKey("user.id"),primary_key=True)
    book_id = db.Column(db.Integer,db.ForeignKey("book.id"),primary_key=True)
    content = db.Column(db.Text,nullable=False)

    def __repr__(self):
        return f"Comment({self.user_id},{self.book_id})"
    
class Rating(db.Model):
    __tablename__ = "rating"

    book_id = db.Column(db.Integer,db.ForeignKey("book.id"),primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey("user.id"),primary_key=True)
    score = db.Column(db.Integer, nullable = False)

    def __repr__(self):
        return f"Rating({self.user_id},{self.book_id})"

class Borrow(db.Model):
    __tablename__ = "borrow"

    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    b_date = db.Column(db.DateTime, nullable = False, default = date.today())

    book = db.relationship('Book',lazy= True)

    def __repr__(self):
        return f"Borrow({self.user_id},{self.book_id},{self.b_date})"
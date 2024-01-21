from moneta.database import db 
from datetime import date

class User(db.Model):
    __tablename__ = "user"

    # Fields
    id = db.Column(db.Integer,primary_key = True)
    username = db.Column(db.Integer,nullable=False,unique=True)
    password = db.Column(db.String(60),nullable=False)
    email = db.Column(db.String(60),nullable=False,unique=True)

    # Reference to all the books currently borrowed
    books = db.relationship('Book',secondary='borrow',lazy=True)

    def __repr__(self):
        return f"User({self.username},{self.email})"

class Role(db.Model):
    __tablename__ = "role"

class Book(db.Model):
    __tablename__ = "book"

    # Fields
    id = db.Column(db.Integer,primary_key = True)
    name = db.Column(db.String(80), unique = True, nullable = False)
    content = db.Column(db.Text,nullable = False)

    # Mass loading of all ratings for particular book avoided due to bulk.

    def __repr__(self):
        return f'Book({self.name})'

class Section(db.Model):
    __tablename__ = "section"

    # Fields
    id = db.Column(db.Integer,primary_key = True)
    name = db.Column(db.String(40), unique = True, nullable = False)
    doc = db.Column(db.DateTime, default = date.today())
    description = db.Column(db.String(256))

    # Mass loading of all books of particular section avoided due to bulk.

    def __repr__(self):
        return f"Section({self.name}, {self.description})"

# Table to store category relation between Book and Section
category = db.Table('category',
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
    db.Column('section_id', db.Integer, db.ForeignKey('section.id'), primary_key=True)
)

# Table to keep track of borrow relation between User and Book
borrow = db.Table('borrow',
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('b_date', db.DateTime, nullable = False, default = date.today())
)

# Table to keep track of rating relation between User and Book
rating = db.Table('rating',
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('score', db.Integer, nullable = False)
)
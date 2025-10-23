from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.orm import relationship
from datetime import datetime,timedelta
db = SQLAlchemy()
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    name = db.Column(db.String(64), nullable=True)
    occupation = db.Column(db.String(64), nullable=True)
    def check_password(self, password):
        return self.password == password

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(80), nullable=False)
    author = db.Column(db.String(64), nullable=False)
    isbn = db.Column(db.String(64), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id', ondelete='CASCADE'),nullable=False)
    section = relationship('Section', backref='section_books', lazy=True, single_parent=True)
    file_path = db.Column(db.String(255)) 
    good_count = db.Column(db.Integer, default=0)
    bad_count = db.Column(db.Integer, default=0)

class Section(db.Model):
    __tablename__ = 'sections'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    date_created = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(120), nullable=False)
    
class Borrowing(db.Model):
    __tablename__ = 'borrowing'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id', ondelete='CASCADE'), nullable=False)
    request_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    return_date = db.Column(db.DateTime, nullable=True)
    user = db.relationship('User', backref='borrowings')
    book = db.relationship('Book', backref='borrowings')

class Completed(db.Model):
    __tablename__ = 'completed'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    feedback = db.Column(db.String(10))
    #relationship with the Book model
    book = db.relationship('Book', backref='completed')
    user = db.relationship('User', backref='completed')
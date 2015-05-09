from __init__ import *
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import UserMixin
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from flask import request
import hashlib, datetime

db = SQLAlchemy()

# Table of Team Member
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), index=True, nullable=False)
    password = db.Column(db.String(25))
    password_hash = db.Column(db.String(128))
    stu_id = db.Column(db.String(20))
    gender = db.Column(db.Boolean)
    email = db.Column(db.String(65))
    create_time = db.Column(db.DateTime)

    def __init__(self, name, password, stu_id, gender, email):
        self.name = name
        self.password = password
        self.stu_id = stu_id
        self.gender = gender
        self.email = email
        self.create_time = datetime.datetime.now()

    def __repr__(self):
        return '<User %s>' % self.name

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def gravatar(self, size=100, default='identicon', rating='g'):
        url = 'http://gravatar.duoshuo.com/avatar'
        hash = hashlib.md5(self.name.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def save(self):
        db.session.add(self)
        db.session.commit()


def db_delete(tuple):
    db.session.delete(tuple)
    #db.session.commit()
from __init__ import *
from dbBase import db
import datetime
# Table of Account
class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)
    solved_or_rating = db.Column(db.Integer, nullable=False, default=0)
    submitted_or_max_rating = db.Column(db.Integer, nullable=False, default=0)
    # update_status
    # 0 for update finished
    # 1 for not init
    # 2 for wait for update
    # 3 for update error
    update_status = db.Column(db.Integer, default=1, index=True)
    oj_name = db.Column(db.String(20), nullable=False)
    last_update_time = db.Column(db.DateTime)
    # connect to User
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('account', lazy='dynamic'))

    def __init__(self, oj_name, nickname, password_or_oj_id, user):
        self.oj_name = oj_name
        self.nickname = nickname
        self.password = password_or_oj_id
        self.last_update_time = datetime.datetime.now()
        self.user = user

    def __repr__(self):
        #return '<Account %s>' % self.nickname
        return '<%s Account %s>: %d / %d' % (self.oj_name, self.nickname, self.solved, self.submitted)

    def set_problem_count(self, v1, v2):
        self.solved_or_rating = v1
        self.submitted_or_max_rating = v2

    def get_problem_count(self):
        if self.oj_name in ['cf', 'bc']:
            return  {'rating': self.solved_or_rating, 'max_rating': self.submitted_or_max_rating}
        else:
            return {'solved': self.solved_or_rating, 'submitted': self.submitted_or_max_rating}

    def save(self):
        db.session.add(self)
        db.session.commit()

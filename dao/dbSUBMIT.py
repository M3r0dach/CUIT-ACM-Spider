from __init__ import *
from dbBase import db

class Submit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pro_id = db.Column(db.String(12))
    run_id = db.Column(db.String(20))
    submit_time = db.Column(db.DateTime)
    run_time = db.Column(db.Integer)
    memory = db.Column(db.Integer)
    lang = db.Column(db.String(20))
    result = db.Column(db.String(100))
    code = db.Column(db.Text)
    update_status = db.Column(db.Integer)
    oj_name = db.Column(db.String(20), nullable=False)
    user_name = db.Column(db.String(25),nullable=True)
    # connect to Account
    account_id = db.Column(db.Integer,db.ForeignKey('account.id'))
    account = db.relationship('Account', backref=db.backref('submit', lazy='dynamic'))



    def __init__(self, pro_id, account):
        self.pro_id = pro_id
        self.account = account
        self.oj_name = account.oj_name
        self.user_name = account.user.name
        self.update_status = 0

    def update_info(self,run_id,submit_time, run_time, memory,lang,code,result):
        self.code = code
        self.run_id = run_id
        self.submit_time = submit_time
        self.run_time = run_time
        self.memory = memory
        self.lang = lang
        self.result = result
        self.save()

    def __repr__(self):
        return '<BNU Submit> \t"%s" \t%s \t%sMS \t%sKB \t%s \t%s' \
               % (self.account_name, self.pro_id, self.run_time, self.memory, self.lang, self.submit_time)


    def save(self):
        db.session.add(self)

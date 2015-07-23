from dao.db import db
from dao.dbBase import User
from flask import Flask
import datetime
import sys
import time
from multiprocessing import Process
from threading import Thread, RLock
import logging
from logging import FileHandler
from logging import Formatter
from dao.dbACCOUNT import Account, AccountStatus
from dao.dbSUBMIT import Submit
from spider.CFSpider import CFSpider
from spider.HDUSpider import HDUSpider
from spider.POJSpider import POJSpider
from spider.ZOJSpider import ZOJSpider
from spider.UVASpider import UVASpider
from spider.BNUSpider import BNUSpider
from spider.BCSpider import BCSpider
from spider.VJSpider import VJSpider
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import or_


app = Flask(__name__)
app.config.from_pyfile('config.py')
db.init_app(app)
file_handler = FileHandler(app.root_path+"/log/spider_errors.log")
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'))
app.logger.addHandler(file_handler)
spider_lock = RLock()

class AccountUpdateServer(Thread):

    def __init__(self,  oj_name):
        Thread.__init__(self)
        self.oj_name = oj_name
        self.spider_module_name = sys.modules['spider.' + self.oj_name.upper()+'Spider']
        self.spider_class_name = oj_name.upper()+'Spider'
        self.spider = getattr(self.spider_module_name, self.spider_class_name)()

    def get_an_available_account(self):
        spider_lock.acquire()
        try:
            permit_date = datetime.datetime.now() - datetime.timedelta(hours=app.config['SERVER_TIME_DELTTA'])
            query = Account.query.filter(Account.oj_name==self.oj_name)
            query = query.filter(Account.update_status!=AccountStatus.UPDATING)
            query = query.filter(or_(Account.last_update_time<permit_date,Account.update_status!=AccountStatus.NORMAL))
            account = query.order_by(Account.last_update_time.asc()).with_lockmode('update').first()
            if not account:
                db.session.commit()
                return
            else:
                self.origin_status = account.update_status
                account.update_status = AccountStatus.UPDATING
                account.save()
                return account
        except:
            pass
        finally:
            spider_lock.release()

    def do_spy(self, account, init):
        self.spider.set_account(account)
        if hasattr(self.spider, 'update_account'):
            self.spider.update_account(init)
        user = User.query.filter(User.id == account.user_id).with_lockmode('update').first()
        user.update()

    def run(self):
        while True:
            with app.app_context():
                try:
                    account = self.get_an_available_account()
                    if not account:
                        time.sleep(10)
                        continue
                    init = True if self.origin_status  == AccountStatus.NOT_INIT else False

                    try:
                        self.do_spy(account, init)
                        account.update_status = AccountStatus.NORMAL
                    except Exception, e:
                        db.session.rollback()
                        account.last_update_time = datetime.datetime.now()
                        account.update_status = AccountStatus.NOT_INIT if self.origin_status == AccountStatus.NOT_INIT else AccountStatus.UPDATE_ERROR
                        app.logger.error('['+self.oj_name+'] update account error! :' + e.message)
                    finally:
                        db.session.commit()
                except Exception, e:
                    db.session.rollback()
                    db.session.commit()
                    app.logger.error('['+self.oj_name+'] update error! :' + e.message)
                time.sleep(60)
                     

if __name__ == '__main__':
    ProcessMap = {}
    for oj in ['bnu','cf','bc','uva','hdu','poj','zoj','vj']:
        ProcessMap[oj+'AccountUpdateServer'] = AccountUpdateServer(oj)
        ProcessMap[oj+'AccountUpdateServer'].start()


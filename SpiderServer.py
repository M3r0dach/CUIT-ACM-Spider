from dao.dbBase import User, db
from flask import Flask
import datetime
import sys
import time
from multiprocessing import Process
from threading import Thread
import logging
from logging import FileHandler
from logging import Formatter
from dao.dbACCOUNT import Account
from dao.dbSUBMIT import Submit
from spider.CFSpider import CFSpider
from spider.HDUSpider import HDUSpider
from spider.POJSpider import POJSpider
from spider.ZOJSpider import ZOJSpider
from spider.UVASpider import UVASpider
from spider.BNUSpider import BNUSpider
from spider.BCSpider import BCSpider
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


class AccountUpdateServer(Thread):

    def  __init__(self,  oj_name):
        Thread.__init__(self)
        self.oj_name = oj_name
        spider_module_name = sys.modules['spider.' + self.oj_name.upper()+'Spider']
        spider_class_name = oj_name.upper()+'Spider'
        self.spider = getattr(spider_module_name,spider_class_name)()

    def run(self):
        while True:
            with app.app_context():
                try:
                    permit_date = datetime.datetime.now() - datetime.timedelta(hours=app.config['SERVER_TIME_DELTTA'])
                    account = Account.query.filter(Account.oj_name==self.oj_name, or_(Account.last_update_time<permit_date,Account.update_status!=0)).with_lockmode('update').first()
                    if not account:
                        db.session.commit()
                        time.sleep(10)
                        continue
                    init =  True if account.update_status==1 or account.update_status==3 else False
                    try:
                        self.spider.set_account(account)
                        if hasattr(self.spider,'update_account'):
                            self.spider.update_account()
                        if hasattr(self.spider,'update_submit'):
                            self.spider.update_submit(init)
                        account.update_status = 0
                    except Exception, e:
                        app.logger.error('['+self.oj_name+'] update account error! :' + e.message)
                        account.update_status = 3
                    finally:
                        account.save()
                except Exception, e:
                    app.logger.error('['+self.oj_name+'] update error! :' + e.message)
                time.sleep(4)


if __name__ == '__main__':
    ProcessMap = {}
    for oj in ['bnu','cf','bc','uva']:
        ProcessMap[oj+'AccountUpdateServer'] = AccountUpdateServer(oj)
        ProcessMap[oj+'AccountUpdateServer'].start()


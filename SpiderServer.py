from dao.dbBase import User, db
from flask import Flask
import sys
import time
from multiprocessing import Process
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

app = Flask(__name__)
app.config.from_pyfile('config.py')
db.init_app(app)
file_handler = FileHandler(app.root_path+"/log/spider_errors.log")
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'))
app.logger.addHandler(file_handler)


class AccountUpdateServer():

    def  __init__(self,  oj_name):
        self.oj_name = oj_name
        spider_module_name = sys.modules['spider.' + self.oj_name.upper()+'Spider']
        spider_class_name = oj_name.upper()+'Spider'
        self.spider = getattr(spider_module_name,spider_class_name)

        account_module_name = sys.modules['dao.dbACCOUNT']
        submit_module_name = sys.modules['dao.dbSUBMIT']
        account_class_name = 'Account'
        submit_class_name = 'Submit'
        self.account_table = getattr(account_module_name,account_class_name)
        self.submit_table = getattr(submit_module_name,submit_class_name)

    def run(self):
        while True:
            with app.app_context():
                try:
                    account = self.account_table.query.filter(self.account_table.update_status!=0,self.account_table.oj_name==self.oj_name).first()
                    if not account or account.update_status==2:
                        time.sleep(1)
                        continue
                    account.update_status = 2
                    account.save()
                    try:
                        spider_instance = self.spider(account.nickname, account.password)
                        spider_instance.login()
                        if spider_instance.login_status == True:
                            count = spider_instance.get_problem_count()
                            account.set_problem_count(count['solved'], count['submitted'])
                            if self.submit_table:
                                if hasattr(spider_instance,'get_solved_list'):
                                    solved_list = spider_instance.get_solved_list()
                                    for problem in solved_list:
                                        if not self.submit_table.query.filter(self.submit_table.pro_id == problem, self.submit_table.account == account).first():
                                            nwork = self.submit_table(problem, account)
                                            nwork.save()
                                elif hasattr(spider_instance,'get_status_list') :
                                    status_list = spider_instance.get_status_list()
                                    for status in status_list:
                                        if spider_instance.is_gym(status['contest_id']):
                                            continue
                                        if not self.submit_table.query.filter(self.submit_table.pro_id == status['pro_id'], self.submit_table.account == account).count():
                                            nwork = self.submit_table(status['pro_id'], account)
                                            try:
                                                nwork.update_info(
                                                    status['run_id'],
                                                    status['submit_time'],
                                                    status['run_time'],
                                                    status['memory'],
                                                    status['lang'],
                                                    status['code']
                                                )
                                            except Exception, e:
                                                db.session.remove(nwork)
                                                db.session.commit()
                                                raise Exception('['+self.oj_name+'] update submits error! :' + e.message)
                                account.update_status = 0
                                account.save()
                        else :
                            raise Exception('account login error!')
                    except Exception, e:
                        app.logger.error('['+self.oj_name+'] update account error! :' + e.message)
                        account.update_status = 3
                        account.save()
                except Exception, e:
                    app.logger.error('['+self.oj_name+'] update error! :' + e.message)
                time.sleep(1)



class SubmitUpdateServer():

    def  __init__(self, oj_name):
        self.oj_name = oj_name
        spider_module_name = sys.modules['spider.' + self.oj_name.upper()+'Spider']
        spider_class_name = oj_name.upper()+'Spider'
        self.spider = getattr(spider_module_name,spider_class_name)

        account_module_name = sys.modules['dao.dbACCOUNT']
        submit_module_name = sys.modules['dao.dbSUBMIT']
        account_class_name = 'Account'
        submit_class_name = 'Submit'
        self.account_table = None
        self.submit_table = None
        if hasattr(account_module_name,account_class_name):
            self.account_table = getattr(account_module_name,account_class_name)
        if hasattr(submit_module_name,submit_class_name):
            self.submit_table = getattr(submit_module_name,submit_class_name)

    def run(self):
        while True:
            with app.app_context():
                try:
                    work = self.submit_table.query.filter(self.submit_table.update_status!=0,self.submit_table.oj_name==self.oj_name).first()
                    if not work:
                        time.sleep(1)
                        continue
                    work.update_status = 2
                    work.save()
                    try:
                        spider_instance = self.spider(work.account.nickname, work.account.password)
                        spider_instance.login()
                        if spider_instance.login_status == True and hasattr(spider_instance,'get_status'):
                            if self.oj_name != 'cf':
                                status = spider_instance.get_status(work.pro_id)
                                work.update_info(
                                    status['run_id'],
                                    status['submit_time'],
                                    status['run_time'],
                                    status['memory'],
                                    status['lang'],
                                    status['code'],
                                )
                                work.update_status = 0
                        else :
                            raise Exception('account login error!')
                    except Exception, e:
                        app.logger.error( '['+self.oj_name+':'+work.account.nickname+'] update submit error! :' + e.message)
                        work.update_status = 3
                    work.save()
                except Exception, e:
                    app.logger.error('['+self.oj_name+'] update error! :' + e.message)
            time.sleep(1)

if __name__ == '__main__':
    ProcessMap = {}
    for oj in ['bnu', 'hdu', 'poj', 'zoj', 'uva', 'cf', 'bc']:
        ProcessMap[oj+'AccountUpdateServer'] = Process(target=AccountUpdateServer(oj).run)
        ProcessMap[oj+'AccountUpdateServer'].start()

    for oj in ['hdu','bnu','zoj','poj','cf']:
        ProcessMap[oj+'SubmitUpdateServer'] = Process(target=SubmitUpdateServer(oj).run)
        ProcessMap[oj+'SubmitUpdateServer'].start()


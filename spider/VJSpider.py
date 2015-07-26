from __init__ import *
from BaseSpider import BaseSpider
from util.ThreadingPool import ThreadPool
import json
from dao.dbACCOUNT import Account
from sqlalchemy import or_

class VJSpider(BaseSpider):

    def __init__(self):
        BaseSpider.__init__(self)
        self.login_url = 'http://acm.hust.edu.cn/vjudge/user/login.action'

    def login(self):
        data = {'username': self.account.nickname,'password':self.account.password}
        try:
            response = self.urlopen_with_data(self.login_url, urllib.urlencode(data))
            status = response.getcode()
            page = response.read()
            info = json.JSONDecoder().decode(page)
            if (status != 200 and status != 302 or info!='success'):
                return False
            self.login_status = True
            return True
        except Exception, e:
            return False

    def get_problem_count(self):
        try :
            submitted = Submit.query.filter(Submit.oj_name==self.account.oj_name, Submit.user==self.account.user)
            solved = submitted.filter(or_(Submit.result == 'OK', Submit.result == 'Accepted'))
            return {'solved': solved.count(), 'submitted': submitted.count()}
        except Exception, e:
            return {'solved': 0, 'submitted': 0}

    def request_data(self):
        data = {
            'draw':'0',
            'columns[0][data]':'0',
            'columns[0][name]':'',
            'columns[0][searchable]':'true',
            'columns[0][orderable]':'false',
            'columns[0][search][value]':'',
            'columns[0][search][regex]':'false',
            'columns[1][data]':'1',
            'columns[1][name]':'',
            'columns[1][searchable]':'true',
            'columns[1][orderable]':'false',
            'columns[1][search][value]':'',
            'columns[1][search][regex]':'false',
            'columns[2][data]':'2',
            'columns[2][name]':'',
            'columns[2][searchable]':'true',
            'columns[2][orderable]':'false',
            'columns[2][search][value]':'',
            'columns[2][search][regex]':'false',
            'columns[3][data]':'3',
            'columns[3][name]':'',
            'columns[3][searchable]':'true',
            'columns[3][orderable]':'false',
            'columns[3][search][value]':'',
            'columns[3][search][regex]':'false',
            'columns[4][data]':'4',
            'columns[4][name]':'',
            'columns[4][searchable]':'true',
            'columns[4][orderable]':'false',
            'columns[4][search][value]':'',
            'columns[4][search][regex]':'false',
            'columns[5][data]':'5',
            'columns[5][name]':'',
            'columns[5][searchable]':'true',
            'columns[5][orderable]':'false',
            'columns[5][search][value]':'',
            'columns[5][search][regex]':'false',
            'columns[6][data]':'6',
            'columns[6][name]':'',
            'columns[6][searchable]':'true',
            'columns[6][orderable]':'false',
            'columns[6][search][value]':'',
            'columns[6][search][regex]':'false',
            'columns[7][data]':'7',
            'columns[7][name]':'',
            'columns[7][searchable]':'true',
            'columns[7][orderable]':'false',
            'columns[7][search][value]':'',
            'columns[7][search][regex]':'false',
            'columns[8][data]':'8',
            'columns[8][name]':'',
            'columns[8][searchable]':'true',
            'columns[8][orderable]':'false',
            'columns[8][search][value]':'',
            'columns[8][search][regex]':'false',
            'columns[9][data]':'9',
            'columns[9][name]':'',
            'columns[9][searchable]':'true',
            'columns[9][orderable]':'false',
            'columns[9][search][value]':'',
            'columns[9][search][regex]':'false',
            'columns[10][data]':'10',
            'columns[10][name]':'',
            'columns[10][searchable]':'true',
            'columns[10][orderable]':'false',
            'columns[10][search][value]':'',
            'columns[10][search][regex]':'false',
            'columns[11][data]':'11',
            'columns[11][name]':'',
            'columns[11][searchable]':'true',
            'columns[11][orderable]':'false',
            'columns[11][search][value]':'',
            'columns[11][search][regex]':'false',
            'order[0][column]':'0',
            'order[0][dir]':'desc',
            'start':'0',
            'length':'20',
            'search[value]':'',
            'search[regex]':'false',
            'un':self.account.nickname,
            'OJId':'All',
            'probNum':'',
            'res':'0',
            'language':'',
            'orderBy':'run_id',
        }
        return data

    def update_submit(self,init=True,length=30):
        baseurl = 'http://acm.hust.edu.cn/vjudge/problem/fetchStatus.action?'
        data = self.request_data()
        data['length'] = str(length)
        while True:
            url = baseurl + urllib.urlencode(data)
            try:
                page = self.load_page(url)
                info = json.JSONDecoder().decode(page)
                if info['data'].__len__() == 0:
                    return
                for status in info['data']:
                    ret = {'pro_id': status[12],
                           'run_id': status[0],
                           'submit_time': datetime.datetime.fromtimestamp(long(str(status[8])[0:-3])),
                           'run_time': status[5],
                           'memory': status[4],
                           'lang': status[6],
                           'result': status[3]
                    }
                    if ret['run_time'] == '':
                        ret['run_time'] = '-1'
                    if ret['memory'] == '':
                        ret['memory'] = '-1'
                    nsub = Submit.query.filter(Submit.run_id == ret['run_id'], Submit.oj_name == self.account.oj_name).first()
                    if nsub and not init:
                        return
                    if not nsub:
                        ret['code'] = self.get_solved_code(ret['run_id'])
                        nsub = Submit(ret['pro_id'], self.account)
                        nsub.update_info(ret['run_id'],ret['submit_time'],ret['run_time'],ret['memory'],ret['lang'],ret['code'],ret['result'])
            except Exception, e:
                db.session.rollback()
                raise Exception('update Status Error:' + e.message)
            data['start'] = str(int(data['start']) + length)
            if init:db.session.commit()
            time.sleep(1)
        self.account.last_update_time = datetime.datetime.now()
        db.session.commit()

    def get_solved_code(self, run_id):
        url = 'http://acm.hust.edu.cn/vjudge/problem/viewSource.action?id={0}'.format(run_id)
        try:
            page = self.load_page(url)
            soup = BeautifulSoup(page, 'html5lib')
            code = soup.find('pre').text
            return code
        except Exception, e:
            raise Exception("Virtual Judge crawl code error " + e.message)

    def update_account(self, init):
        if not self.account:
            raise Exception("Virtual Judge account not set")
        self.login()
        if not self.login_status:
            raise Exception("Virtual Judge account login failed")
        self.update_submit(init)
        count = self.get_problem_count()
        self.account.set_problem_count(count['solved'], count['submitted'])
        self.account.last_update_time = datetime.datetime.now()
        self.account.save()
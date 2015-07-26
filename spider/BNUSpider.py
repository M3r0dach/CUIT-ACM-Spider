from __init__ import *
from BaseSpider import BaseSpider
from util.ThreadingPool import ThreadPool
import json

class BNUSpider(BaseSpider):

    def __init__(self):
        BaseSpider.__init__(self)
        self.login_url = 'http://acm.bnu.edu.cn/v3/ajax/login.php'

    def login(self):
        data = {'username': self.account.nickname,'password':self.account.password, 'cksave':'1'}
        try:
            response = self.urlopen_with_data(self.login_url, urllib.urlencode(data))
            status = response.getcode()
            page = response.read()
            info = json.JSONDecoder().decode(page)
            if (status != 200 and status != 302 or info['code']!=0):
                return False
            self.login_status = True
            return True
        except Exception, e:
            return False

    def get_problem_count(self):
        url = 'http://acm.bnu.edu.cn/v3/userinfo.php?name=' + self.account.nickname
        try :
            page = self.load_page(url)
            soup = BeautifulSoup(page, 'html5lib')
            submitted = soup.find('th', text='Total Submissions').next_sibling.next_sibling.text
            solved = soup.find('th', text='Accepted').next_sibling.next_sibling.text
            return {'solved': solved, 'submitted': submitted}
        except Exception, e:
            return {'solved': 0, 'submitted': 0}

    def get_solved_list(self):
        url = 'http://acm.bnu.edu.cn/v3/userinfo.php?name=' + self.account.nickname
        try :
            page = self.load_page(url)
            soup = BeautifulSoup(page, 'html5lib')
            pro_set = soup.select('#userac > a')
            ret = []
            for pro in pro_set:
                ret.append(pro.text)
            return ret
        except Exception, e:
            raise Exception('Get Solved List ERROR:' + e.message)

    def request_data(self):
        data = {
            'sEcho' : '4',
            'iColumns' : '10',
            'sColumns' : '',
            'iDisplayStart' : '0',
            'iDisplayLength' : '30',
            'mDataProp_0' : '0',
            'mDataProp_1' : '1',
            'mDataProp_2' : '2',
            'mDataProp_3' : '3',
            'mDataProp_4' : '4',
            'mDataProp_5' : '5',
            'mDataProp_6' : '6',
            'mDataProp_7' : '7',
            'mDataProp_8' : '8',
            'mDataProp_9' : '9',
            'sSearch' : '',
            'bRegex' : 'false',
            'sSearch_0' : self.account.nickname,
            'bRegex_0' : 'false',
            'bSearchable_0' : 'true',
            'sSearch_1' : '',
            'bRegex_1' : 'false',
            'bSearchable_1' : 'true',
            'sSearch_2' : '',
            'bRegex_2' : 'false',
            'bSearchable_2' : 'true',
            'sSearch_3' : '',
            'bRegex_3' : 'false',
            'bSearchable_3' : 'true',
            'sSearch_4' : '',
            'bRegex_4' : 'false',
            'bSearchable_4' : 'true',
            'sSearch_5' : '',
            'bRegex_5' : 'false',
            'bSearchable_5' : 'true',
            'sSearch_6' : '',
            'bRegex_6' : 'false',
            'bSearchable_6' : 'true',
            'sSearch_7' : '',
            'bRegex_7' : 'false',
            'bSearchable_7' : 'true',
            'sSearch_8' : '',
            'bRegex_8' : 'false',
            'bSearchable_8': 'true',
            'sSearch_9' : '',
            'bRegex_9' : 'false',
            'bSearchable_9' : 'true',
            'iSortCol_0' : '1',
            'sSortDir_0' : 'desc',
            'iSortingCols' : '1',
            'bSortable_0':'false',
            'bSortable_1':'false',
            'bSortable_2':'false',
            'bSortable_3':'false',
            'bSortable_4':'false',
            'bSortable_5':'false',
            'bSortable_6':'false',
            'bSortable_7':'false',
            'bSortable_8':'false',
            'bSortable_9':'false',
        }
        return data

    def update_submit(self,init=True,length=30):
        baseurl = 'http://acm.bnu.edu.cn/v3/ajax/status_data.php?'
        data = self.request_data()
        data['iDisplayLength'] = str(length)
        while True:
            url = baseurl + urllib.urlencode(data)
            try:
                page = self.load_page(url)
                info = json.JSONDecoder().decode(page)
                if info['aaData'].__len__() == 0:
                    return
                for status in info['aaData']:
                    ret = {'pro_id': status[2],
                           'run_id': status[1],
                           'submit_time': status[8],
                           'run_time': status[5][:-3],
                           'memory': status[6][:-3],
                           'lang': status[4],
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
            data['iDisplayStart'] = str(int(data['iDisplayStart']) + length)
            if init:db.session.commit()
            time.sleep(1)
        self.account.last_update_time = datetime.datetime.now()
        db.session.commit()

    def get_solved_code(self, run_id):
        url = 'http://acm.bnu.edu.cn/v3/ajax/get_source.php?runid='+run_id
        try:
            page = self.load_page(url)
            info = json.JSONDecoder().decode(page)
            return BeautifulSoup(info['source'], 'html5lib').text
        except Exception, e:
            raise Exception("BNU crawl code error " + e.message)

    def update_account(self, init):
        if not self.account:
            raise Exception("BNU account not set")
        self.login()
        if not self.login_status:
            raise Exception("BNU account login failed")
        count = self.get_problem_count()
        self.account.set_problem_count(count['solved'], count['submitted'])
        self.account.last_update_time = datetime.datetime.now()
        self.account.save()
        self.update_submit(init)

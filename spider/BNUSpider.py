from __init__ import *
from BaseSpider import BaseSpider
from dao.dbBNU import BnuSubmit
from util.ThreadingPool import ThreadPool
import json

class BNUSpider(BaseSpider):

    def __init__(self,username='', password=''):
        BaseSpider.__init__(self)
        self.login_url = 'http://acm.bnu.edu.cn/v3/ajax/login.php'
        self.username = username
        self.password = password
        self.login_status = False

    def login(self):
        data = {'username': self.username,'password':self.password, 'cksave':'1'}
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
        url = 'http://acm.bnu.edu.cn/v3/userinfo.php?name=' + self.username
        try :
            page = self.load_page(url)
            soup = BeautifulSoup(page)
            submitted = soup.find('th', text='Total Submissions').next_sibling.next_sibling.text
            solved = soup.find('th', text='Accepted').next_sibling.next_sibling.text
            return {'solved': solved, 'submitted': submitted}
        except Exception, e:
            return {'solved': 0, 'submitted': 0}

    def get_solved_list(self):
        url = 'http://acm.bnu.edu.cn/v3/userinfo.php?name=' + self.username
        try :
            page = self.load_page(url)
            soup = BeautifulSoup(page)
            pro_set = soup.select('#userac > a')
            ret = []
            for pro in pro_set:
                ret.append(pro.text)
            return ret
        except Exception, e:
            raise Exception('Get Solved List ERROR:' + e.message)

    def get_status(self, pro_id):
        url = 'http://acm.bnu.edu.cn/v3/ajax/status_data.php?'
        data = {
            'sEcho' : '4',
            'iColumns' : '10',
            'sColumns' : '',
            'iDisplayStart' : '0',
            'iDisplayLength' : '1',
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
            'sSearch_0' : self.username,
            'bRegex_0' : 'false',
            'bSearchable_0' : 'true',
            'sSearch_1' : '',
            'bRegex_1' : 'false',
            'bSearchable_1' : 'true',
            'sSearch_2' : pro_id,
            'bRegex_2' : 'false',
            'bSearchable_2' : 'true',
            'sSearch_3' : 'Accepted',
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
        url = url + urllib.urlencode(data)
        try:
            page = self.load_page(url)
            info = json.JSONDecoder().decode(page)
            status = info['aaData'][0]
            ret = {'pro_id': pro_id,
                   'run_id': status[1],
                   'submit_time': status[8],
                   'run_time': status[5][:-3],
                   'memory': status[6][:-3],
                   'lang': status[4]}
            ret['code'] = self.get_solved_code(ret['run_id'])
            if ret['memory'] == '':
                ret['memory'] = '-1'
            return ret
        except Exception, e:
            raise Exception('Get Status Error:' + e.message)

    def get_status_list(self, account):
        solved_list = self.get_solved_list()
        for problem in solved_list:
            status = self.get_status(problem)
            if status:
                self.submit_status(status, account)

    def submit_status(self, status, account):
        try:
            submit = BnuSubmit(status['pro_id'],
                               account)
            submit.save()
        except Exception, e:
            raise Exception("Submit to DB Error!!!" + e.message)

    def get_solved_code(self, run_id):
        url = 'http://acm.bnu.edu.cn/v3/ajax/get_source.php?runid='+run_id
        try :
            page = self.load_page(url)
            info = json.JSONDecoder().decode(page)
            return BeautifulSoup(info['source']).text
        except Exception, e:
            return ''

    def save(self, account):
        self.login()
        count = self.get_problem_count()
        account.set_problem_count(count['solved'], count['submitted'])
        account.save()
        self.get_status_list(account)

def test():
    spider = BNUSpider('dreameracm','3235083')
    spider.login()
    spider.get_problem_count()
    spider.get_solved_list()
    print spider.get_status('1000')

if __name__ == '__main__':
    start = time.time()
    test()
    print time.time() - start
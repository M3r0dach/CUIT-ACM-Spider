from __init__ import *
from BaseSpider import BaseSpider
from util.ThreadingPool import ThreadPool

class POJSpider(BaseSpider):

    def __init__(self):
        BaseSpider.__init__(self)
        self.login_url = 'http://poj.org/login'

    def login(self):
        data = {'user_id1': self.account.nickname, 'password1': self.account.password, 'B1': 'login', 'url': '/'}
        try:
            response = self.urlopen_with_data(self.login_url, urllib.urlencode(data))
            status = response.getcode()
            page = response.read()
            if (status != 200 and status != 302) or page.find('Log Out') == -1:
                return False
            self.login_status = True
            return True
        except Exception, e:
            return False

    def fix_problem_id(self, string):
        start = string.find('(') + 1
        return string[start:]

    def get_problem_count(self):
        url = 'http://poj.org/userstatus?user_id='+self.account.nickname
        try:
            page = self.load_page(url)
            soup = BeautifulSoup(page, 'html5lib')
            solved = soup.find(text='Solved:').parent.next_sibling.next_sibling.text
            submitted = soup.find(text='Submissions:').parent.next_sibling.next_sibling.text
            return {'solved': solved, 'submitted': submitted}
        except Exception, e:
            raise Exception('Get Problem Count Error:' + e.message)

    def get_solved_list(self):
        url = 'http://poj.org/userstatus?user_id='+self.account.nickname
        try_time = 3
        while try_time:
            try :
                page = self.load_page(url)
                soup = BeautifulSoup(page, 'html5lib')
                pro_set = soup.select('script')[1].text.split('}')[1]
                if pro_set:
                    problem_list = pro_set.split(')')
                    ret = []
                    for problem in problem_list:
                        if problem =='' or problem.strip() =='':
                            continue
                        problem_id = self.fix_problem_id(problem)
                        if not problem_id.isdigit():
                            raise Exception('GET Problem Id Failed')
                        ret.append(problem_id)
                    return ret
                else:
                    return []
            except Exception, e:
                time.sleep(10)
            try_time -= 1
        return []

    def get_status(self, start):
        url = 'http://poj.org/status?user_id={0}&top={1}'.format(self.account.nickname, start)
        try_time = 3
        slist = []
        while try_time:
            try:
                page = self.load_page(url)
                soup = BeautifulSoup(page, 'html5lib')
                tds = soup.select('tr[align="center"]')#[2].select('td')
                for td in tds:
                    status = []
                    index = 0
                    for value in td:
                        if index in [0, 2, 3, 4, 5, 6, 8]:
                            status.append(value.text)
                        index += 1
                    ret = {'pro_id': status[1], 'run_id': status[0], 'submit_time': status[6], 'run_time': status[4][:-2],
                           'memory': status[3][:-1], 'lang': status[5], 'result': status[2]}
                    ret['code'] = self.get_solved_code(ret['run_id'])
                    if ret['run_time'] == '':
                        ret['run_time'] = '-1'
                    if ret['memory'] == '':
                        ret['memory'] = '-1'
                    slist.append(ret)
                return slist
            except Exception, e:
                time.sleep(10)
            try_time -= 1
        raise Exception('Get Status Error:')

    def get_solved_code(self, run_id):
        url = 'http://poj.org/showsource?solution_id='+run_id
        try_time = 3
        while try_time:
            try :
                page = self.load_page(url)
                soup = BeautifulSoup(page, 'html5lib')
                return soup.find('pre').text
            except Exception, e:
                time.sleep(5)
            try_time-=1
        raise Exception("crawl code error")

    def update_submit(self, init):
        start = ''
        while True:
            slist = self.get_status(start)
            if not slist:
                return
            try:
                for status in slist:
                    nsub = Submit.query.filter(Submit.run_id == status['run_id'], Submit.oj_name == self.account.oj_name).first()
                    if nsub and not init:
                        return
                    if not nsub:
                        nsub = Submit(status['pro_id'], self.account)
                        nsub.update_info(status['run_id'],status['submit_time'],status['run_time'],status['memory'],status['lang'],status['code'],status['result'])
            except Exception, e:
                db.session.rollback()
                raise Exception('update Status Error:' + e.message)
            if init:
                db.session.commit()
            time.sleep(2)
            start = slist[-1]['run_id']
        self.account.last_update_time = datetime.datetime.now()
        db.session.commit()

    def update_account(self, init):
        if not self.account:
            raise Exception("POJ account not set")
        self.login()
        if not self.login_status:
            raise Exception("POJ account login failed")
        count = self.get_problem_count()
        self.account.set_problem_count(count['solved'], count['submitted'])
        self.account.last_update_time = datetime.datetime.now()
        self.account.save()
        self.update_submit(init)


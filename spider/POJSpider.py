from __init__ import *
from BaseSpider import BaseSpider
from util.ThreadingPool import ThreadPool

class POJSpider(BaseSpider):

    def __init__(self, username='', password=''):
        BaseSpider.__init__(self)
        self.login_url = 'http://poj.org/login'
        self.username = username
        self.password = password
        self.login_status = False

    def login(self):
        data = {'user_id1': self.username, 'password1': self.password, 'B1': 'login', 'url': '/'}
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
        url = 'http://poj.org/userstatus?user_id='+self.username
        try:
            page = self.load_page(url)
            soup = BeautifulSoup(page)
            solved = soup.find(text='Solved:').parent.next_sibling.next_sibling.text
            submitted = soup.find(text='Submissions:').parent.next_sibling.next_sibling.text
            return {'solved': solved, 'submitted': submitted}
        except Exception, e:
            raise Exception('Get Problem Count Error:' + e.message)

    def get_solved_list(self):
        url = 'http://poj.org/userstatus?user_id='+self.username
        try_time = 3
        while try_time:
            try :
                page = self.load_page(url)
                soup = BeautifulSoup(page)
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

    def get_status(self, pro_id):
        url = 'http://poj.org/status?problem_id='+pro_id+'&user_id='+self.username+'&result=0'
        try_time = 3
        while try_time:
            try:
                page = self.load_page(url)
                soup = BeautifulSoup(page)
                tds = soup.select('tr[align="center"]')[0]
                status = []
                index = 0
                for value in tds:
                    if index in [0, 4, 5, 6, 8]:
                        status.append(value.text)
                    index += 1
                ret = {'pro_id': pro_id,
                       'run_id': status[0],
                       'submit_time': status[4],
                       'run_time': status[2][:-2],
                       'memory': status[1][:-1],
                       'lang': status[3]}
                ret['code'] = self.get_solved_code(ret['run_id'])
                return ret
            except Exception, e:
                time.sleep(10)
            try_time -= 1
        return None

    def get_solved_code(self, run_id):
        url = 'http://poj.org/showsource?solution_id='+run_id
        try :
            page = self.load_page(url)
            soup = BeautifulSoup(page)
            return soup.find('pre').text
        except Exception, e:
            raise Exception("crawl code error " + e.message)

    def update_account(self, account):
        self.login()
        if not self.login_status:
            return False
        count = self.get_problem_count()
        account.set_problem_count(count['solved'], count['submitted'])
        account.last_update_time = datetime.datetime.now()
        account.save()
        solved_list = self.get_solved_list()
        for problem in solved_list:
            if not Submit.query.filter(Submit.pro_id == problem, Submit.account == account).first():
                nwork = Submit(problem, account)
                nwork.save()


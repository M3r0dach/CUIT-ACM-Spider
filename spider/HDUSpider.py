from __init__ import *
from BaseSpider import BaseSpider
from util.ThreadingPool import ThreadPool


class HDUSpider(BaseSpider):

    def __init__(self, username='', password=''):
        BaseSpider.__init__(self)
        self.login_url = 'http://acm.hdu.edu.cn/userloginex.php?action=login'
        self.username = username
        self.password = password
        self.login_status = False

    def login(self):
        data = {'username': self.username, 'userpass': self.password, 'login': 'Sign In'}
        try:
            response = self.urlopen_with_data(self.login_url, urllib.urlencode(data))
            status = response.getcode()
            page = response.read()
            if (status != 200 and status != 302) or page.find('Sign Out') == -1:
                return False
            self.login_status = True
            return True
        except Exception, e:
            return False

    def fix_problem_id(self, string):
        start = string.find('(') + 1
        end = string.find(',')
        return string[start:end]

    def get_problem_count(self):
        url = 'http://acm.hdu.edu.cn/userstatus.php?user='+self.username
        try:
            page = self.load_page(url)
            soup = BeautifulSoup(page)
            solved = soup.find(text='Problems Solved').parent.next_sibling.text
            submitted = soup.find(text='Problems Submitted').parent.next_sibling.text
            return {'solved': solved, 'submitted': submitted}
        except Exception, e:
            raise Exception('Get Problem Count Error:' + e.message)

    def get_solved_list(self):
        url = 'http://acm.hdu.edu.cn/userstatus.php?user='+self.username
        try:
            page = self.load_page(url)
            soup = BeautifulSoup(page)
            pro_set = soup.select('p > script')[0].text
            if pro_set:
                problem_list = pro_set.split(';')
                ret = []
                for problem in problem_list:
                    if problem == '':
                        continue
                    problem_id = self.fix_problem_id(problem)
                    if not problem_id.isdigit():
                        raise Exception('GET Problem Id Failed')
                    ret.append(problem_id)
                return ret
            else:
                return []
        except Exception , e:
            raise Exception('Get Solved List ERROR:' + e.message)

    def get_status(self, pro_id):
        url = 'http://acm.hdu.edu.cn/status.php?user='+self.username+'&pid='+pro_id+'&status=5'
        try:
            page = self.load_page(url)
            soup = BeautifulSoup(page)
            tds = soup.select('tr[align="center"]')[2].select('td')
            status = []
            index = 0
            for value in tds:
                if index in [0, 1, 4, 5, 7]:
                    status.append(value.contents[0])
                index += 1
            ret = {'pro_id': pro_id,
                   'run_id': status[0],
                   'submit_time': status[1],
                   'run_time': status[2][:-2],
                   'memory': status[3][:-1],
                   'lang': status[4]}
            ret['code'] = self.get_solved_code(ret['run_id'])
            return ret
        except Exception, e:
            raise Exception('Get Status Error:' + e.message)

    def get_status_list(self, account):
        solved_list = self.get_solved_list()
        for problem in solved_list:
            status = self.get_status(problem)
            if status:
                self.submit_status(status, account)


    def get_solved_code(self, run_id):
        url = 'http://acm.hdu.edu.cn/viewcode.php?rid='+run_id
        try :
            page = self.load_page(url)
            soup = BeautifulSoup(page)
            return soup.find('textarea').text
        except Exception ,e :
            return u''


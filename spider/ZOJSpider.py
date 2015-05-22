from __init__ import *
from BaseSpider import BaseSpider
from util.ThreadingPool import ThreadPool

class ZOJSpider(BaseSpider):

    def __init__(self, username='', password=''):
        BaseSpider.__init__(self)
        self.login_url = 'http://acm.zju.edu.cn/onlinejudge/login.do'
        self.username = username
        self.password = password
        self.status_url = ''
        self.login_status = False

    def login(self):
        data = {'handle': self.username, 'password': self.password}
        try:
            response = self.urlopen_with_data(self.login_url,urllib.urlencode(data))
            status = response.getcode()
            page = response.read()
            if (status != 200 and status != 302) or page.find('Logout') == -1:
                return False
            self.get_user_status_href()
            self.login_status = True
            return True
        except Exception, e:
            return False

    def get_user_status_href(self):
        url = 'http://acm.zju.edu.cn/onlinejudge'
        page = self.load_page(url)
        soup = BeautifulSoup(page)
        href =  soup.select('td > a')[1].attrs.get('href')
        self.status_url ='http://acm.zju.edu.cn' + href


    def get_problem_count(self):
        try :
            url = self.status_url
            page = self.load_page(url)
            soup = BeautifulSoup(page)
            ac_ratio = soup.find(text='AC Ratio:').parent.next_sibling.next_sibling.text.strip().split('/')

            return {'solved': ac_ratio[0], 'submitted': ac_ratio[1]}
        except Exception, e:
            raise Exception('get problem count error '+ e.message)

    def get_solved_list(self):
        try:
            url = self.status_url
            page = self.load_page(url)
            soup = BeautifulSoup(page)
            pro_set = soup.find_all(href = re.compile('problemCode'))
            ret = []
            for problem in pro_set:
                ret.append(problem.text)
            return ret
        except Exception, e:
            raise Exception('Get Solved List ERROR:' + e.message)

    def get_status(self, pro_id):
        url = 'http://acm.zju.edu.cn/onlinejudge/showRuns.do?contestId=1&search=true&firstId=-1&lastId=-1&problemCode=%s&handle=%s&idStart=&idEnd=&judgeReplyIds=5' % (pro_id ,self.username)
        page = self.load_page(url)
        try :
            soup = BeautifulSoup(page)
            tds = soup.select('.list > tr:nth-of-type(2) > td')
            status = []
            index = 0
            code_url = tds[4].contents[0].attrs['href']
            for value in tds:
                if index in [0 ,1, 4, 5, 6]:
                    status.append(value.text)
                index += 1
            ret = {'pro_id': pro_id,
                   'run_id': status[0],
                   'submit_time': status[1],
                   'run_time': status[3],
                   'memory': status[4],
                   'lang': status[2]}
            ret['code'] = self.get_solved_code(code_url)
            return ret
        except Exception , e:
            raise Exception('Get Status Error:' + e.message)

    def get_solved_code(self, code_url):
        url = 'http://acm.zju.edu.cn'+code_url
        try :
            page = self.load_page(url)
            return page
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


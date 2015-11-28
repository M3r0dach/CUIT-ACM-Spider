from __init__ import *
from BaseSpider import BaseSpider, LoginFailedException
from util.ThreadingPool import ThreadPool

class ZOJSpider(BaseSpider):

    def __init__(self):
        BaseSpider.__init__(self)
        self.login_url = 'http://acm.zju.edu.cn/onlinejudge/login.do'
        self.status_url = ''

    def login(self):
        data = {'handle': self.account.nickname, 'password': self.account.password}
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
        soup = BeautifulSoup(page, 'html5lib')
        href = soup.select('td > a')[1].attrs.get('href')
        self.status_url ='http://acm.zju.edu.cn' + href


    def get_problem_count(self):
        try:
            url = self.status_url
            page = self.load_page(url)
            soup = BeautifulSoup(page, 'html5lib')
            ac_ratio = soup.find(text='AC Ratio:').parent.next_sibling.next_sibling.text.strip().split('/')

            return {'solved': ac_ratio[0], 'submitted': ac_ratio[1]}
        except Exception, e:
            raise Exception('get problem count error '+ e.message)

    def get_solved_list(self):
        try:
            url = self.status_url
            page = self.load_page(url)
            soup = BeautifulSoup(page, 'html5lib')
            pro_set = soup.find_all(href=re.compile('problemCode'))
            ret = []
            for problem in pro_set:
                ret.append(problem.text)
            return ret
        except Exception, e:
            raise Exception('Get Solved List ERROR:' + e.message)

    def get_status(self, start):
        url = 'http://acm.zju.edu.cn/onlinejudge/showRuns.do?contestId=1&search=true&lastId={0}&handle={1}'.format(start, self.account.nickname)
        page = self.load_page(url)
        slist = []
        try:
            soup = BeautifulSoup(page, 'html5lib')
            trs = soup.select('.list > tbody > tr')
            for tr in trs:
                status = []
                if tr.attrs.get('class')[0] == 'rowHeader':
                    continue
                tds = tr.select('td')
                for value in tds:
                    status.append(value.text.strip())
                ret = {'pro_id': status[3], 'run_id': status[0], 'submit_time': status[1], 'run_time': status[5],
                       'memory': status[6], 'lang': status[4], 'result': status[2]}
                codeurl = tds[4].contents[0].attrs.get('href')
                ret['code'] = self.get_solved_code(codeurl)
                if ret['run_time'] == '':
                    ret['run_time'] = '-1'
                if ret['memory'] == '':
                    ret['memory'] = '-1'
                slist.append(ret)
            return slist
        except Exception, e:
            raise Exception('Get Status Error:' + e.message)

    @try_times(3)
    def get_solved_code(self, code_url):
        url = 'http://acm.zju.edu.cn'+code_url
        try:
            page = self.load_page(url)
            return page
        except Exception, e:
            raise Exception("crawl code error " + e.message)

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
            raise Exception("ZOJ account not set")
        self.login()
        if not self.login_status:
            raise LoginFailedException("ZOJ account login failed")
        count = self.get_problem_count()
        self.account.set_problem_count(count['solved'], count['submitted'])
        self.account.last_update_time = datetime.datetime.now()
        self.account.save()
        self.update_submit(init)
        self.logout()


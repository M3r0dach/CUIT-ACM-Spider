from __init__ import *
from BaseSpider import BaseSpider
from dao.dbACCOUNT import Account
from util.ThreadingPool import ThreadPool


class HDUSpider(BaseSpider):

    def __init__(self):
        BaseSpider.__init__(self)
        self.login_url = 'http://acm.hdu.edu.cn/userloginex.php?action=login'

    def login(self):
        data = {'username': self.account.nickname, 'userpass': self.account.password, 'login': 'Sign In'}
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
        url = 'http://acm.hdu.edu.cn/userstatus.php?user='+self.account.nickname
        try:
            page = self.load_page(url)
            soup = BeautifulSoup(page, 'html5lib')
            solved = soup.find(text='Problems Solved').parent.next_sibling.text
            submitted = soup.find(text='Problems Submitted').parent.next_sibling.text
            return {'solved': solved, 'submitted': submitted}
        except Exception, e:
            raise Exception('Get Problem Count Error:' + e.message)

    def get_solved_list(self):
        url = 'http://acm.hdu.edu.cn/userstatus.php?user='+self.account.nickname
        try:
            page = self.load_page(url)
            soup = BeautifulSoup(page, 'html5lib')
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
        except Exception, e:
            raise Exception('Get Solved List ERROR:' + e.message)

    def get_status(self, start):
        url = 'http://acm.hdu.edu.cn/status.php?user={0}&first={1}'.format(self.account.nickname, start)
        slist = []
        try:
            page = self.load_page(url)
            soup = BeautifulSoup(page, 'html5lib')
            tds = soup.select('.table_text > tbody > tr[align=center]')#[2].select('td')
            for td in tds:
                status = []
                index = 0
                for value in td:
                    if index in [0, 1, 2, 3, 4, 5, 7]:
                        status.append(value.text)
                    index += 1
                ret = {'pro_id': status[3], 'run_id': status[0], 'submit_time': status[1], 'run_time': status[4][:-2],
                       'memory': status[5][:-1], 'lang': status[6], 'result': status[2]}
                ret['code'] = self.get_solved_code(ret['run_id'])
                slist.append(ret)
            return slist
        except Exception, e:
            raise Exception('Get Status Error:' + e.message)


    def get_solved_code(self, run_id):
        url = 'http://acm.hdu.edu.cn/viewcode.php?rid='+run_id
        try:
            page = self.load_page(url)
            soup = BeautifulSoup(page, 'html5lib')
            return soup.find('textarea').text
        except Exception, e:
            raise Exception("crawl code error "+run_id + e.message)

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
            start = str(int(slist[-1]['run_id'])-1)
        self.account.last_update_time = datetime.datetime.now()
        db.session.commit()

    def update_account(self, init):
        if not self.account:
            raise Exception("HDU account not set")
        self.login()
        if not self.login_status:
            raise Exception("HDU account login failed")
        count = self.get_problem_count()
        self.account.set_problem_count(count['solved'], count['submitted'])
        self.account.last_update_time = datetime.datetime.now()
        self.account.save()
        self.update_submit(init)
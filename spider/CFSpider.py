from __init__ import *
from BaseSpider import BaseSpider
import json, time

class CFSpider(BaseSpider):

    def __init__(self):
        BaseSpider.__init__(self)
        self.login_status = True

    def get_user_info(self):
        url = 'http://codeforces.com/api/user.info?handles='+self.account.nickname
        page = self.load_page(url)
        try:
            info = json.JSONDecoder().decode(page)
            status =  info['status']
            if status == 'OK':
                result = info['result'][0]
                return result
            else:
                return None
        except Exception, e:
            raise Exception('GET USER INFO FAILED:' + e.message)

    def get_problem_count(self):
        user_info = self.get_user_info()
        ret = {'solved': user_info['rating'],
               'submitted': user_info['maxRating']}
        return ret

    def get_status(self, start, length):
        url = 'http://codeforces.com/api/user.status?handle={0}&from={1}&count={2}'.format(self.account.nickname, start, length)
        page = self.load_page(url)
        try:
            info = json.JSONDecoder().decode(page)
            status = info['status']
            if status == 'OK':
                return info['result']
            else:
                return []
        except Exception, e:
            raise Exception('GET STATUES ERROR:' + e.message)

    def is_gym(self, contest_id):
        if len(str(contest_id)) > 3:
            return True
        return False

    def get_status_list(self, start=1, length=30):
        submits = self.get_status(start, length)
        slist = []
        try:
            for submit in submits:
                if self.is_gym(submit['contestId']):
                    continue
                submit_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(submit['creationTimeSeconds']))
                cur = {'contest_id': submit['contestId'],
                       'pro_index': submit['problem']['index'],
                       'run_id': submit['id'],
                       'submit_time': submit_time,
                       'run_time': submit['timeConsumedMillis'],
                       'memory': submit['memoryConsumedBytes'] / 1024,
                       'lang': submit['programmingLanguage'],
                       'result': submit['verdict']
                }
                cur['pro_id'] = str(cur['contest_id']) + str(cur['pro_index'])
                cur['code'] = 'http://codeforces.com/contest/'+str(cur['contest_id'])+'/submission/'+str(cur['run_id'])
                slist.append(cur)
            return slist
        except Exception, e:
            raise Exception('GET STATUS LIST ERROR: ' + e.message)

    def get_solved_code(self, contest_id, run_id):
        url = 'http://codeforces.com/contest/'+str(contest_id)+'/submission/'+str(run_id)
        page = self.load_page(url)
        print url
        try:
            soup = BeautifulSoup(page)
            return soup.find('pre').text
        except Exception, e:
            raise Exception("CF crawl code error " + e.message)

    def update_submit(self, init=True, length=30):
        start = 1
        while True:
            slist = self.get_status_list(start)
            if not slist:
                return
            try:
                for status in slist:
                    if self.is_gym(status['contest_id']):
                        continue
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
            time.sleep(1)
            start += length
        self.account.last_update_time = datetime.datetime.now()
        db.session.commit()

    def update_account(self, init):
        if not self.account:
            raise Exception("CF account not set")
        count = self.get_problem_count()
        self.account.set_problem_count(count['solved'], count['submitted'])
        self.account.last_update_time = datetime.datetime.now()
        self.account.save()
        self.update_submit(init)



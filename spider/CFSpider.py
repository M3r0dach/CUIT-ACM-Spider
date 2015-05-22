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

    def get_status(self):
        url = 'http://codeforces.com/api/user.status?handle='+self.account.nickname
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

    def is_gym(self,contest_id):
        if len(str(contest_id)) > 3:
            return True
        return False


    def get_status_list(self, verdict='OK'):
        submits = self.get_status()
        list = []
        try:
            for submit in submits:
                submit_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(submit['creationTimeSeconds']))
                cur = {'contest_id': submit['contestId'],
                       'pro_index': submit['problem']['index'],
                       'run_id': submit['id'],
                       'submit_time': submit_time,
                       'run_time': submit['timeConsumedMillis'],
                       'memory': submit['memoryConsumedBytes'] / 1024,
                       'lang': submit['programmingLanguage']
                }
                cur['pro_id'] = str(cur['contest_id']) + str(cur['pro_index'])
                cur['code'] = 'http://codeforces.com/contest/'+str(cur['contest_id'])+'/submission/'+str(cur['run_id'])
                list.append(cur)
            return list
        except Exception, e:
            raise Exception('GET STATUS LIST ERROR: ' + e.message)

    def get_solved_code(self, contest_id, run_id):
        url = 'http://codeforces.com/contest/'+str(contest_id)+'/submission/'+str(run_id)
        page = self.load_page(url)
        try:
            soup = BeautifulSoup(page)
            return soup.find('pre').text
        except Exception, e:
            raise Exception("crawl code error " + e.message)


    def update_account(self):
        if not self.account:
            return
        count = self.get_problem_count()
        self.account.set_problem_count(count['solved'], count['submitted'])
        self.account.last_update_time = datetime.datetime.now()
        self.account.save()



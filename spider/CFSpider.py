from __init__ import *
from BaseSpider import BaseSpider
from dao.dbCF import CfSubmit
import json, time

class CFSpider(BaseSpider):

    def __init__(self, handle='', password=''):
        BaseSpider.__init__(self)
        self.handle = handle
        self.login_status = True

    def set_handle(self, handle):
        self.handle = handle

    def get_user_info(self):
        url = 'http://codeforces.com/api/user.info?handles='+self.handle
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
        url = 'http://codeforces.com/api/user.status?handle='+self.handle
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

    def submit_status(self, status, account):
        try:
            submit = CfSubmit(status['contest_id'],
                              status['pro_index'],
                              status['run_id'],
                              status['submit_time'],
                              status['run_time'],
                              status['memory'],
                              status['lang'],
                              account)
            submit.save()
        except Exception, e:
            raise Exception("Submit to DB Error!!!: " + e.message)

    def get_status_list(self, verdict='OK'):
        submits = self.get_status()
        list = []
        try:
            for submit in submits:
                if submit['verdict'] != verdict:
                    continue
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
        except:
            return ''

    def save(self, account):
        rating = self.get_problem_count()
        account.set_problem_count(rating['rating'], rating['max_rating'])
        account.save()
        status_list = self.get_status_list()
        for status in status_list:
            self.submit_status(status, account)




from __init__ import *
from BaseSpider import BaseSpider
from dao.dbACCOUNT import Account
import json

class BCSpider(BaseSpider):

    def __init__(self):
        BaseSpider.__init__(self)

    def get_problem_count(self):
        url = 'http://bestcoder.hdu.edu.cn/api/api.php?type=user-rating&user='+self.account.nickname
        try:
            page = self.load_page(url)
            data = json.JSONDecoder().decode(page)
            try:
                rating = data[-1]['rating']
                max_rating = max(data , key = lambda x: x['rating'])['rating']
            except:
                rating = max_rating = 0
            return {'solved': rating, 'submitted': max_rating}
        except Exception, e:
            raise Exception('Get Problem Count Error:' + e.message)

    def update_account(self, init):
        if not self.account:
            raise Exception('BestCoder Account Not Set')
        count = self.get_problem_count()
        self.account.set_problem_count(count['solved'], count['submitted'])
        self.account.last_update_time = datetime.datetime.now()
        self.account.save()
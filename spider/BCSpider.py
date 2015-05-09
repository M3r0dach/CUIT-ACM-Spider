from __init__ import *
from BaseSpider import BaseSpider

class BCSpider(BaseSpider):

    def __init__(self, username='', userpass=''):
        BaseSpider.__init__(self)
        self.username = username
        self.login_status = True #True

    def get_problem_count(self):
        url = 'http://bestcoder.hdu.edu.cn/rating.php?user='+self.username
        try:
            page = self.load_page(url)
            soup = BeautifulSoup(page)
            info_elements = soup.find(text='Rating: ').parent.next_sibling.next_sibling.text.split(' ')
            rating = info_elements[0]
            max_rating = info_elements[2][:-1]
            return {'solved': rating, 'submitted': max_rating}
        except Exception, e:
            raise Exception('Get Problem Count Error:' + e.message)

    def save(self, account):
        count = self.get_problem_count()
        account.set_problem_count(count['rating'], count['max_rating'])
        account.save()


from __init__ import *
from BaseSpider import BaseSpider

class UVASpider(BaseSpider):

    def __init__(self, username='', user_id=''):
        BaseSpider.__init__(self)
        self.login_url = 'http://uva.onlinejudge.org/index.php?option=com_comprofiler&task=login'
        self.username = username
        self.user_id = user_id
        self.login_status = True

    #def get_login_hidden_params(self):
    #    index_page = self.load_page('http://uva.onlinejudge.org/')
    #    try:
    #        params = {}
    #        soup = BeautifulSoup(index_page, "lxml")
    #        hidden_params_doc = soup.find_all("input", type="hidden")
    #        for item in hidden_params_doc:
    #            key = item.attrs.get('name')
    #            value = item.attrs.get('value')
    #            params[key] = value
    #        return params
    #
    #    except Exception, e:
    #        print 'GET UVA LOGIN PARAMS ERROR!' + e.message
    #        return {}

    #def login(self):
    #    login_hidden_params = self.get_login_hidden_params()
    #    data = dict({'username': self.username, 'passwd': self.password, 'Submit':'Login', 'remember':'yes'},**login_hidden_params)
    #    try:
    #        response = self.urlopen_with_data(self.login_url, urllib.urlencode(data))
    #        status = response.getcode()
    #        page = response.read()
    #        if (status != 200 and status != 302) or page.find('Logout') == -1:
    #            print 'Login Failed!'
    #       W     return False
    #        self.login_status = True
    #        return True
    #    except Exception, e:
    #        print 'Login Error:' + e.message
    #        return False

    def get_problem_count(self):
        url = 'http://uva.onlinejudge.org/index.php?option=com_onlinejudge&Itemid=20&page=show_authorstats&userid='+self.user_id
        try:
            page = self.load_page(url)
            soup = BeautifulSoup(page)
            info_element = soup.find(text='SUBMISSIONS').parent.parent.previous_sibling.previous_sibling
            submitted =  info_element.contents[1].text
            solved = info_element.contents[3].text
            return {'solved': solved, 'submitted': submitted}
        except Exception, e:
            raise Exception('Get Problem Count Error:' + e.message)

    def save(self, account):
        count = self.get_problem_count()
        account.set_problem_count(count['solved'], count['submitted'])
        account.save()



def test():
    spider = UVASpider(user_id='324331')
    print spider.get_problem_count()

if __name__ == '__main__':
    start = time.time()
    test()
    print time.time() - start
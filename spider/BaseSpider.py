import urllib2, urllib
import cookielib


class BaseSpider():
    def __init__(self):
        self.user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.115 Safari/537.36"
        self.headers =  {'User-Agent': self.user_agent}
        self.cookieJar = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookieJar), urllib2.HTTPHandler)
        urllib2.install_opener(self.opener)
        self.login_status = False

    def set_user_agent(self, user_agent):
        self.user_agent = user_agent

    def set_account(self, account):
        self.login_status = False
        self.cookieJar.clear()
        self.account = account

    def login(self):
        pass


    def load_page(self, url):
        req = urllib2.Request(url, headers=self.headers)
        page = ''
        try:
            response = urllib2.urlopen(req, timeout=20)
            page = response.read()
            return page
        except urllib2.HTTPError, e:
            raise Exception('Open the request Failed!:', e.code, url)
        except urllib2.URLError, e:
            raise Exception('Open the url Failed!:', e.reason, url)
        except Exception, e:
            raise Exception('Open the page Failed!:' + e.message)

    def urlopen_with_data(self, url,  post_data):
        req = urllib2.Request(url, post_data, headers=self.headers)
        try:
            response = urllib2.urlopen(req, timeout=20)
            return response
        except Exception, e:
            raise Exception('Open the url Failed:' + e.message)
from app.spiders import Spider


class HduSpider(Spider):
    login_url = 'http://acm.hdu.edu.cn/userloginex.php?action=login'

    def __init__(self):
        super(HduSpider, self).__init__()

        pass

    def login(self):
        pass

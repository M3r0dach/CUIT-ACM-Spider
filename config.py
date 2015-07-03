
#The database URI that should be used for the connection.
#fomate: dialect+driver://username:password@host:port/database
#mysql format : mysql://scott:tiger@localhost/database_name
SQLALCHEMY_DATABASE_URI = 'mysql://root:zzyacmer@localhost/oj_helper_test'

#A dictionary that maps bind keys to SQLAlchemy connection URIs.
SQLALCHEMY_BINDS = {}

ADMIN = ['Rayn', 'dreameracm']

OJ_MAP = {
    'hdu': 'HDU',
    'cf': 'Codeforces',
    'bc': 'BestCoder',
    'poj': 'POJ',
    'uva': 'UVA',
    'zoj': 'ZOJ',
    'bnu': 'BNU'
}

SERVER_TIME_DELTTA = 6

CSRF_ENABLED = True
SECRET_KEY = 'a very hard string'


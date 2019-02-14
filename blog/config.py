USERNAME = 'root'
PASSWD = 'qwe123'
IP = '127.0.0.1'
PORT = 3306
DBNAME = 'blog'
PARAMS = 'charset=utf8'
URL = 'mysql+pymysql://{}:{}@{}:{}/{}?{}'.format(USERNAME, PASSWD, IP, PORT, DBNAME, PARAMS)

DATABASE_DEBUG = True

WSIP = '127.0.0.1'
WSPORT = 9000

AUTH_SECRET='www.magedu.com'
AUTH_EXPIRE = 8*60*60
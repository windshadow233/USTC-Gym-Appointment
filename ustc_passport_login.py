import requests
from bs4 import BeautifulSoup


class USTCPassportLogin(object):
    def __init__(self):
        self.passport = "https://passport.ustc.edu.cn/login"
        self.sess = requests.session()
        self.sess.headers = {
            "User-Agent": 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
        }

    def _get_cas_lt(self):
        """
        获取登录时需要提供的验证字段
        """
        response = self.sess.get(self.passport)
        CAS_LT = BeautifulSoup(response.text, 'lxml').find(attrs={'id': 'CAS_LT'}).get('value')
        return CAS_LT

    def login(self, username, password):
        """
        登录,需要提供用户名、密码
        """
        self.sess.cookies.clear()
        try:
            CAS_LT = self._get_cas_lt()
            login_data = {
                'username': username,
                'password': password,
                'warn': '',
                'CAS_LT': CAS_LT,
                'showCode': '',
                'button': '',
                'model': 'uplogin.jsp',
                'service': '',
            }
            self.sess.post(self.passport, login_data, allow_redirects=False)
            return self.sess.cookies.get("uc") == username
        except Exception as e:
            print(e)
            return False

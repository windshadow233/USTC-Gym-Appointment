import requests
from bs4 import BeautifulSoup
import cv2
import os
from PIL import Image
import time
import numpy as np
import pytesseract


class USTCPassportLogin(object):
    def __init__(self):
        self.passport = "https://passport.ustc.edu.cn/login"
        self.validate_url = "https://passport.ustc.edu.cn/validatecode.jsp?type=login"
        self.sess = requests.session()
        # 验证码图片存放路径
        self.LT_save_path = '/tmp'
        # 验证码图片文件名
        self.LT_file = ''
        # 验证码识别结果
        self.LT = ''

    def _get_cas_lt(self):
        """
        获取登录时需要提供的验证字段
        """
        response = self.sess.get(self.passport)
        CAS_LT = BeautifulSoup(response.text, 'lxml').find(attrs={'id': 'CAS_LT'}).get('value')
        return CAS_LT

    def _save_validate_number(self):
        """
        将验证码图片保存到一个文件
        """
        validate_number = self.sess.get(self.validate_url)
        self.LT_file = str(time.time()) + '.jpg'
        with open(os.path.join(self.LT_save_path, self.LT_file), 'wb') as f:
            f.write(validate_number.content)

    def _recognize_validate_number(self):
        """
        识别验证码
        """
        image = cv2.imread(os.path.join(self.LT_save_path, self.LT_file))
        kernel = np.ones((2, 2), np.uint8)
        image = cv2.dilate(image, kernel, iterations=1)
        image = Image.fromarray(image).convert('L')
        config = '--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789'
        self.LT = pytesseract.image_to_string(image, config=config).strip()
        return self.LT

    def login(self, username, password):
        """
        登录,需要提供用户名、密码
        """
        self.sess.cookies.clear()
        self.LT_file = ''
        self.LT = ''
        try:
            CAS_LT = self._get_cas_lt()
            self._save_validate_number()
            self._recognize_validate_number()
            login_data = {
                'username': username,
                'password': password,
                'warn': '',
                'CAS_LT': CAS_LT,
                'showCode': '1',
                'button': '',
                'model': 'uplogin.jsp',
                'service': '',
                'LT': self.LT
            }
            self.sess.post(self.passport, login_data, allow_redirects=False)
            return self.sess.cookies.get("uc") == username
        except:
            return False

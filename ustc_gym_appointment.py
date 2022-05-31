import datetime
import json
import urllib.parse
import asyncio
import aiocqhttp
import yaml

from ustc_passport_login import USTCPassportLogin


class USTCGymAppointment(object):
    def __init__(self):
        self.login_bot = USTCPassportLogin()
        self.sess = self.login_bot.sess
        self.cas_url = 'https://passport.ustc.edu.cn/login?service=https://cgyy.ustc.edu.cn/validateLogin.html'
        self.token_url = 'https://cgyy.ustc.edu.cn/api/user/login'
        self.submit_url = 'https://cgyy.ustc.edu.cn/api/app/appointment/record/submit'
        self.cancel_url = 'https://cgyy.ustc.edu.cn/api/app/appointment/record/cancel/'

        self.token = ''

        self.id2time = {
            3: "08:00-09:30",
            4: "09:30-11:00",
            5: "11:00-12:30",
            6: "12:30-14:00",
            7: "14:00-15:30",
            8: "15:30-17:00",
            9: "17:00-18:30",
            10: "18:30-20:00",
            11: "20:00-21:30"
        }

    def _get_ticket(self):
        response = self.sess.get(self.cas_url, allow_redirects=False)
        url = response.headers.get('Location')
        params = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))
        return params.get('ticket')

    def _get_token(self, ticket):
        """
        获取token
        """
        headers = {"content-type": "application/json"}
        data = {
            "ticket": ticket
        }
        r = self.sess.post(self.token_url, data=json.dumps(data), headers=headers)
        return r.json().get('data').get('token')

    def _login(self, username, password):
        """
        登录,需要提供用户名、密码，顺便返回后续表单需要提供的token
        """
        self.token = ''
        is_success = self.login_bot.login(username, password)
        if is_success:
            ticket = self._get_ticket()
            self.token = self._get_token(ticket)
        return is_success

    @aiocqhttp.ensure_async
    def submit(self, gymnasium_id, sport_place_id, time_quantum_id,
               user, people_number, appointment_day, phone, success_list):
        post_data = {
            "gymnasiumId": gymnasium_id,
            "sportPlaceId": sport_place_id,
            "timeQuantum": self.id2time[time_quantum_id],
            "timeQuantumId": time_quantum_id,
            "appointmentUserName": user,
            "appointmentPeopleNumber": people_number,
            "appointmentDay": appointment_day,
            "phone": phone
        }
        headers = {
            "content-type": "application/json",
            "token": self.token
        }
        result = self.sess.post(self.submit_url, data=json.dumps(post_data), headers=headers).json()
        code = result.get('code')
        if code != 200:
            print(f"{post_data['timeQuantum']}, 场地{sport_place_id}", result.get('msg'), "\n")
            return False, result.get('msg')
        data = result.get('data')
        data['time'] = post_data['timeQuantum']
        success_list.append(data)
        return True, data

    def cancel(self, username, password, reserve_id):
        """
        取消预约，需要提供账号密码，操作ID
        """
        self.sess.cookies.clear()
        login_status = self._login(username, password)
        if login_status:
            print("Login successfully!")
        else:
            print("Login failed!")
            return
        url = self.cancel_url + str(reserve_id)
        headers = {
            "content-type": "application/json",
            "token": self.token
        }
        r = self.sess.post(url, headers=headers).json()
        return r.get('code') == 200, r.get('msg')

    def appointment(self, file="config.yml"):
        if datetime.datetime.now().hour < 22:
            print("Not available time!")
            return
        with open(file, encoding='utf-8') as f:
            data = yaml.safe_load(f)
        username = data['username']
        password = data['password']
        time_ids = data['time_ids']
        self.sess.cookies.clear()
        login_status = self._login(username, password)
        if login_status:
            print("Login successfully!")
        else:
            print("Login failed!")
            return
        people_number = data.get('people_number', 2)
        gymnasium_id = 1
        date = (datetime.datetime.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        tasks = []
        success_list = []
        for time_id in time_ids:
            for place in range(1, 15):
                tasks.append(self.submit(gymnasium_id=gymnasium_id,
                                         sport_place_id=place,
                                         time_quantum_id=time_id,
                                         user='',
                                         people_number=people_number,
                                         appointment_day=date,
                                         phone='',
                                         success_list=success_list))
        t = asyncio.gather(*tasks)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(t)
        if not success_list:
            print('Available place not found!')
        for success_item in success_list:
            print(f"预约成功\n此次操作ID为: {success_item.get('id')}(可用于取消预约), 您的入场码为: {success_item.get('code')}, "
                  f"场地: {success_item.get('placeName')}, 入场时间: {date} {success_item.get('time')}, "
                  f"入场人数: {people_number}")

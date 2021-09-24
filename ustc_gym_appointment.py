import datetime
import json
import urllib.parse
import tqdm

from ustc_passport_login import USTCPassportLogin


class USTCGymAppointment(object):
    def __init__(self):
        self.login_bot = USTCPassportLogin()
        self.sess = self.login_bot.sess
        self.cas_url = 'https://passport.ustc.edu.cn/login?service=https://cgyy.ustc.edu.cn/validateLogin.html'
        self.info_url = 'https://cgyy.ustc.edu.cn/api/app/sport/place/getAppointmentInfo'
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
        self.time2id = dict(zip(self.id2time.values(), self.id2time.keys()))

    def _get_ticket(self):
        response = self.sess.get(self.cas_url, allow_redirects=False)
        url = response.headers.get('Location')
        params = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))
        return params.get('ticket')

    def _get_token(self, ticket):
        """
        获取token
        """
        headers = {
            "content-type": "application/json"
        }
        data = {
            "ticket": ticket
        }
        r = self.sess.post(self.token_url, data=json.dumps(data), headers=headers)
        return r.json().get('data').get('token')

    def _get_available(self, gymnasium_id, date_str, time_quantum_id):
        """
        寻找某一天某一时间段的可用场地
        """
        data = {
            "gymnasiumId": gymnasium_id,
            "dateStr": date_str,
            "timeQuantumId": time_quantum_id
        }
        headers = {"content-type": "application/json"}
        result = self.sess.post(self.info_url, data=json.dumps(data), headers=headers).json()
        code = result.get('code')
        if code != 200:
            return False, result.get('msg')
        available = [data.get('id') for data in result.get('data') if data.get('useType') == 0]
        return True, available

    def _choose_sport(self):
        """
        选择羽毛球或游泳
        """
        print('目前游泳预约已切换平台，强制选择羽毛球')
        return 1
        while 1:
            choise = input("选择想要预约的运动类型:\n0: 退出\n1: 羽毛球\n2: 游泳") or '1'
            if choise.isdigit() and int(choise) in {0, 1, 2}:
                break
        if choise == '0':
            return
        return {'1': 1, '2': 4}.get(choise)

    def _choose_date(self, available_dict):
        dates = list({key[0] for key in available_dict.keys()})
        dates.sort()
        msg = f"请选择预约日期:\n0: 退出\n"
        for i, date in enumerate(dates, 1):
            msg += f'{i}: {date}\n'
        while 1:
            choise = input(msg) or '1'
            if choise.isdigit() and int(choise) in range(i + 1):
                break
        if choise == '0':
            return
        selected_date = dates[int(choise) - 1]
        return selected_date

    def _choose_time(self, available_dict, date):
        times = [key[1] for key in available_dict.keys() if key[0] == date]
        times.sort()
        msg = f"请选择预约时间段:\n0: 退出\n"
        for i, t in enumerate(times, 1):
            msg += f'{i}: {self.id2time[t]}\n'
        while 1:
            choise = input(msg) or '1'
            if choise.isdigit() and int(choise) in range(len(times) + 1):
                break
        if choise == '0':
            return
        return times[int(choise) - 1]

    def _choose_available_place(self, available):
        while 1:
            choise = input(f"可用场地: {available}\n请选择(0: 退出):\n") or str(available[0])
            if choise.isdigit() and (choise == '0' or int(choise) in available):
                return int(choise)

    def _choose_people_number(self, gymnasium_id):
        default = {1: '2', 4: '1'}.get(gymnasium_id)
        while 1:
            people_number = input(f"请填写入场人数(1~10):\n羽毛球默认2人、游泳默认1人\n0: 退出\n") or default
            if people_number.isdigit() and 0 <= int(people_number) <= 10:
                return int(people_number)

    def login(self, username, password):
        """
        登录,需要提供用户名、密码，顺便返回后续表单需要提供的token
        """
        self.token = ''
        is_success = self.login_bot.login(username, password)
        if is_success:
            ticket = self._get_ticket()
            self.token = self._get_token(ticket)
        return is_success

    def find_available(self, gymnasium_id):
        """
        寻找四天内的可用场地
        返回一个字典,其键为(date, time_quantum_id)二元组,值为可用场地的list
        """
        today = datetime.datetime.now()
        one_day = datetime.timedelta(days=1)
        dates = [(today + one_day * i).strftime("%Y-%m-%d") for i in range(4)]
        available_dict = {}
        for date in tqdm.tqdm(dates):
            for time_quantum_id in self.id2time.keys():
                is_success, available = self._get_available(gymnasium_id, date, time_quantum_id)
                if is_success and available:
                    available_dict[(date, time_quantum_id)] = available
        return available_dict

    def submit(self, gymnasium_id, sport_place_id, time_quantum_id,
               user, people_number, appointment_day, phone):
        """
        提交预约请求,需要提供预约表单的参数
        成功时返回预约信息，失败时返回预约失败的msg
        """
        data = {
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
        result = self.sess.post(self.submit_url, data=json.dumps(data), headers=headers).json()
        code = result.get('code')
        if code != 200:
            return False, result.get('msg')
        return True, result.get('data')

    def cancel(self, reserve_id):
        """
        取消预约，需要提供操作ID
        """
        url = self.cancel_url + str(reserve_id)
        headers = {
            "content-type": "application/json",
            "token": self.token
        }
        r = self.sess.post(url, headers=headers).json()
        return r.get('code') == 200, r.get('msg')

    def interact(self):
        """
        简单的人机交互程序
        """
        gymnasium_id = self._choose_sport()
        if not gymnasium_id:
            return
        sport = {1: '羽毛球', 4: '游泳'}.get(gymnasium_id)
        print(f"选定运动类型: {sport}")
        print("正在寻找四天内的可用场地...")
        available = self.find_available(gymnasium_id)
        if not available:
            print("这几天场地已经约满了！")
            return
        date = self._choose_date(available)
        if not date:
            return
        print(f"选定日期: {date}")
        t_id = self._choose_time(available, date)
        if not t_id:
            return
        print(f"选定时间: {self.id2time[t_id]}")
        available = available[(date, t_id)]
        place = self._choose_available_place(available)
        if not place:
            return
        print(f"选定场地号: {place}")
        people_number = self._choose_people_number(gymnasium_id)
        if not people_number:
            return
        is_success, msg = self.submit(gymnasium_id=gymnasium_id,
                                      sport_place_id=place,
                                      time_quantum_id=t_id,
                                      user='',
                                      people_number=people_number,
                                      appointment_day=date,
                                      phone='')
        if not is_success:
            print(f"预约失败: {msg}")
        else:
            print(f"预约成功\n此次操作ID为: {msg.get('id')}(可用于取消预约), 您的入场码为: {msg.get('code')}, 场地: {msg.get('placeName')}, "
                  f"入场时间: {date} {self.id2time[t_id]}, 入场人数: {people_number}")

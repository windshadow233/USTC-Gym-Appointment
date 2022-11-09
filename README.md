# USTC-Gym-Appointment
中科大中区体育中心小程序预约脚本

支持通过统一身份认证登录进行中区体育馆场地预约（由于游泳预约平台已经迁移，目前该脚本只支持预约羽毛球场）

** 羽毛球馆预约平台将于2022/10/7迁移至新平台，因此此仓库源代码将失效 **，<del>新平台预计与游泳预约平台类似，可采用简单的抓包方法获取token。</del>

本项目仅供学习使用

# 环境

python=3.6+

见requirements.txt

# 使用方法

首先在config.yml中填写需要的字段，例如：

```yaml
username: SA66668888
password: 12345678
time_ids: [3, 4, 5, 6]
people_number: 2
```

需要注意:

- 所有字符均须使用半角字符
- 冒号与值之间需要有空格

其中，time_ids为一个list，包含你想预约的全部时间段的id，对应关系如下：

|时间段|id|
|---|---|
|08:00-09:30|3|
|09:30-11:00|4|
|11:00-12:30|5|
|12:30-14:00|6|
|14:00-15:30|7|
|15:30-17:00|8|
|17:00-18:30|9|
|18:30-20:00|10|
|20:00-21:30|11|

例如，若你想预约14:00-21:30之间任意场次，就填: [7, 8, 9, 10, 11]

在配置完文件后，直接按下面方法在当前路径下调用脚本（由于场馆位置紧张，程序设计可运行时间在晚上22:00至23:59之前，抢第二天的位置）：

```shell script
python main.py
```

取消预约方法：
```python
from ustc_gym_appointment import USTCGymAppointment


bot = USTCGymAppointment()
# 通过USTCGymAppointment.cancel方法取消预约,参数reserve_id在预约成功后的返回结果中获取
bot.cancel(username="SA66668888", password="12345678", reserve_id="123456")
```

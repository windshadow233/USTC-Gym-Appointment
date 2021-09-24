# USTC-Gym-Appointment
中科大中区体育中心小程序预约脚本

支持通过统一身份认证登录进行中区体育馆场地预约（由于游泳预约平台已经迁移，目前该脚本只支持预约羽毛球场）

如果你强行令变量gymnasium_id为4，将可以在小程序中获取到一张游泳馆入场券，但我估计这个入场券是无效的

本项目仅供学习使用

# 环境

python=3.6

见requirements.txt

# 使用方法
```python
from ustc_gym_appointment import USTCGymAppointment

bot = USTCGymAppointment()
# 登录
bot.login('SAxxxxxxxx', 'password')
# 可通过简单交互程序进行预约
bot.interact()
# 也可通过bot.submit方法自行调用预约,需要自己构造params参数
bot.submit(params)
# 通过bot.cancel方法取消预约,参数reserve_id在预约成功后的返回结果中获取
bot.cancel(reserve_id)
# 使用bot.find_available方法获取四天内的可用场地
available = bot.find_available(gymnasium_id=1)

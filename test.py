import datetime as DT
dt = DT.datetime.strptime('2019-12-24 04:01:00', '%Y-%m-%d %H:%M:%S')
print(dt)
print(dt.timestamp())
print()
# 2019-12-24 04:00:00
# 1577142000.0

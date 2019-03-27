#!/usr/bin/python
#--*--coding:utf-8--*--

# db_url:223.75.53.43:8089:XE
# user:interface
# passwd:interface12345678

from apscheduler.scheduler import Scheduler

# sched = Scheduler()
# #minutes=1
# @sched.interval_schedule(seconds=5)
def update_host():
    print("定时执行的任务")

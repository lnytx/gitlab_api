# -*- coding:utf-8 -*-


import datetime
import json
import re
import time

import logging

import os

import paramiko
import requests

def get_system_data():
    print("执行get_system_data")
    system_data={}
    url1 = 'http://59.208.149.24:8084/big/zwfw/onlineman.jspx'#获取当前在线人数
    url2 = 'http://59.208.149.24:8084/big/zwfw/rizhouyue/fangwenl.jspx?callback=callback4&_=1553068413578'#获取日访问量
    url3 = 'http://zwfw.hubei.gov.cn/'#政务服务网域名
    # url1 = 'http://192.168.77.21:8084/big/zwfw/onlineman.jspx'#获取当前在线人数
    # url2 = 'http://192.168.77.21:8084/big/zwfw/rizhouyue/fangwenl.jspx?callback=callback4&_=1553068413578'#获取日访问量
    # url3 = 'http://zwfw.hubei.gov.cn/'#政务服务网域名
    ri_pv = requests.get(url2)
    data1 = ri_pv.text
    # {"COMENUM": 124260, "DTIME": "03-21"}]
    #拼接当前日期
    localtime = time.localtime(time.time())
    print("localtime",localtime)
    if localtime.tm_mon<10 and localtime.tm_mday<10:
        re_str = str(0)+str(localtime.tm_mon)+'-0'+str(localtime.tm_mday)
    if localtime.tm_mon<10 and localtime.tm_mday>10:
        re_str = str(0)+str(localtime.tm_mon)+'-'+str(localtime.tm_mday)
    if localtime.tm_mon > 10 and localtime.tm_mday < 10:
        re_str = str(localtime.tm_mon) + '-0' + str(localtime.tm_mday)
    else:#都大于10
        re_str = str(localtime.tm_mon) + '-' + str(localtime.tm_mday)
    print("localtime",re_str)

    if data1 != None and data1 !='':
        a = json.loads(data1[9:].strip('(').strip(')'))
        print("日访问量",a['ridata'])
        for i in a['ridata']:
            for k,v in i.items():
                if str(v) == re_str:
                    print("当天的访问量",i)
                    system_data['current_pv'] = i['COMENUM']
                    break
          # 当日系统访问量
    else:
        system_data['current_pv'] = 0  # 当日系统访问量
    current_uv = requests.get(url1)
    data2 = current_uv.text
    print("data2",data2)
    if data2 != None and data2 !='':
        temp2 = json.loads(data2)
        system_data['current_uv'] = temp2['data']['ONLINENUM']  # 当前在线用户数
    else:
        temp2 = 'null'
        system_data['current_uv'] = 0  # 当前在线用户数
    seconds_list=[]#多访问几次,添加到列表计算最大最小及平均值
    for _ in range(3):
        repose = requests.get(url3)
        # seconds_list.append(repose.elapsed.total_seconds())#单位为秒
        seconds_list.append(repose.elapsed.microseconds / 1000)#单位为毫秒
    system_data['reponse_time'] = repose.elapsed.total_seconds()#url响应时长
    if repose.status_code==None or repose.status_code=='':
        system_data['status_code'] = '未知'#url响应状态码
    else:
        system_data['status_code'] = repose.status_code  # url响应状态码
    system_data['reponse_max_time'] = max(seconds_list)
    system_data['reponse_min_time'] = min(seconds_list)
    system_data['reponse_avg_time'] = sum(seconds_list)/3
    # system_data['seqid'] = get_seq()
    system_data['url'] = url3
    system_data['weburl'] = 'weburl'

if __name__=='__main__':
    get_system_data()








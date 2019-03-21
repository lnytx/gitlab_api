# -*- coding:utf-8 -*-
'''
Created on 2017年8月4日

@author: admin
连接oracle数据库处理数据
'''

import datetime
import json
import re
import time
import pymysql
import logging

import os

import requests

os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'

# 处理多个参数时，计算应该有几个%s的方法
log_file = 'conn_data.log'
logging.basicConfig(filename=log_file, level=logging.DEBUG,
                    format='[%(asctime)s] %(levelname)s [%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filemode='a')


def oracle_connect():
    import cx_Oracle
    # connection = cx_Oracle.connect("user", "password", "TNS")
    # host = '192.168.77.151'#内网IP
    host = '223.75.53.43'  # 外网IP
    port = 8089
    service_name = 'XE'
    try:
        conn = cx_Oracle.connect('interface/interface12345678@%s:%s/%s' % (host, port, service_name))
        logging.info("oracle conn is success!")
        return conn
    except Exception as e:
        logging.error("oracle conn is fails{}".format(e))


def search_table(table_name):
    orcl_conn = oracle_connect()
    orcl_cursor = orcl_conn.cursor()
    orcl_cursor.execute('select * from %s' % table_name)
    result = orcl_cursor.fetchall()  # 获取到了数据结果是个list[(),()]
    logging.info("当表插入%s表，共%s条记录" % (table_name, len(result)))
    orcl_cursor.close()
    orcl_conn.close()
    return result


def execute(sql, data, table_name):  # 执行sql语句，主要是在mysql中执行插入操作
    orcl_conn = oracle_connect()
    orcl_cursor = orcl_conn.cursor()
    logging.info("执行插入表:%s" % table_name)
    start = time.time()
    orcl_cursor.executemany(sql, data)
    orcl_cursor.commit()
    end = time.time()
    orcl_cursor.close()
    orcl_cursor.close()
    logging.info("插入表%s共耗时%s秒" % (table_name, end - start))


if __name__ == '__main__':
    #资源内部id,业务系统1，接口2，中间件3，数据库4
    tables = ['MID_DB_DATA', 'SERVICE_INTERFACE', 'SERVICE_SYSTEM', 'DATA_DICT']
    #数据库数据
    sql_db = "insert into MID_DB_DATA(STATUS,MAXCONNS,CURCONNS,DBNULLSELECTTIME,ID,SEQID) values " \
             "('true','1200','500','10','4',SEQ_ID.NEXTVAL)"
    #中间件数据
    sql_mid = "insert into MID_DB_DATA(STATUS,MAXCONNS,CURCONNS,MIDDLEWARE_JVM,ID,SEQID) values " \
              "('false','200','100','10%','3',SEQ_ID.NEXTVAL)"
    # 业务系统
    sql_system = "insert into SERVICE_SYSTEM(CURUV,CURPV,RESPONSETIME,STATUSCODE,MAXTIME,MINITIME,AVGTIME,BUSINESSNUMBER,INTERFACEURL,SEQID) values " \
    #业务接口
    sql_interface = "insert into SERVICE_INTERFACE(MAXTIME,MINITIME,AVGTIME,INTERFACEURL,URLVV,SEQID) values " \
              "('0.5','0.2','0.5','http://zwfw.hubei.gov.cn/','1000',SEQ_ID.NEXTVAL)"


    # orcl_conn = oracle_connect()
    # orcl_cursor = orcl_conn.cursor()
    # start = time.time()
    # try:
    #     orcl_cursor.execute(sql_interface)
    #     orcl_conn.commit()
    # except Exception as e:
    #     print("插入数据错误",str(e))
    # end = time.time()
    # print("time",end-start)
    # orcl_cursor.close()
    # orcl_conn.close()
    #
    # data = search_table('MID_DB_DATA')
    # print("data", data)
    url1 = 'http://59.208.149.24:8084/big/zwfw/onlineman.jspx'#获取当前在线人数
    url2 = 'http://59.208.149.24:8084/big/zwfw/rizhouyue/fangwenl.jspx?callback=callback4&_=1553068413578'#获取日访问量
    url3 = 'http://zwfw.hubei.gov.cn/'#政务服务网域名
    ri_pv = requests.get(url2)
    data1 = ri_pv.text
    # {"COMENUM": 124260, "DTIME": "03-21"}]
    print("data", type(data1), data1)
    #拼接当前日期
    localtime = time.localtime(time.time())
    print("localtime",localtime)
    re_str = str(0)+str(localtime.tm_mon)+'-'+str(localtime.tm_mday)
    print("本地时间为 :", str(0)+str(localtime.tm_mon)+'-'+str(localtime.tm_mday))
    str1 = data1[759:int(data1.find(re_str))+7]
    print("str2",str1)
    temp1 = json.loads(str1)#获取当日访问量
    current_uv = requests.get(url1)
    data2 = current_uv.text
    temp2 = json.loads(data2)
    # {"COMENUM": 124260, "DTIME": "03-21"}]
    print("temp1",type(temp1),temp1)
    print("temp2",type(temp2),temp2)
    #获取业务响应时间，状态码
    seconds_list=[]#多访问几次计算最大最小平均值
    for _ in range(3):
        repose = requests.get(url3)
        seconds_list.append(repose.elapsed.total_seconds())
    print("响应状态码",repose.status_code)
    print("响应时间",repose.elapsed.total_seconds())
    print("多次访问时间",seconds_list)
    print("最大",max(seconds_list))
    print("最小",min(seconds_list))
    print("平均",men(seconds_list))


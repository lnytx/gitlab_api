# -*- coding:utf-8 -*-
'''
Created on 2017年8月4日

@author: admin
连接oracle数据库处理数据

alter sequence seq_id increment by 1;#重置seq
'''

import datetime
import json
import re
import time

import logging

import os

import paramiko
import requests

from apscheduler.scheduler import Scheduler

'''

'''

# os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'

# 将logging的日志时间修改成北京时间
def beijing(sec, what):
    beijing_time = datetime.datetime.now() + datetime.timedelta(hours=8)
    return beijing_time.timetuple()

logging.Formatter.converter = beijing

log_file = 'conn_app.log'
logging.basicConfig(filename=log_file, level=logging.DEBUG,
                    format='[%(asctime)s] %(levelname)s [%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filemode='a')


def oracle_connect():
    import cx_Oracle
    # connection = cx_Oracle.connect("user", "password", "TNS")
    host = '192.168.77.151'#内网IP
    # host = '223.75.53.43'  # 外网IP
    port = 8089
    service_name = 'XE'
    try:
        conn = cx_Oracle.connect('interface/interface12345678@%s:%s/%s' % (host, port, service_name))
        logging.info("oracle conn is success!")
        return conn
    except Exception as e:
        logging.error("oracle conn is fails{}".format(e))

def get_seq():
    orcl_conn = oracle_connect()
    orcl_cursor = orcl_conn.cursor()
    start = time.time()
    try:
        # 处理业务系统数据
        orcl_cursor.execute('select seq_app.nextval from dual')
        seq_id = orcl_cursor.fetchall()
        return re.sub("\D", "", str(seq_id))
    except Exception as e:
        print("获取seq失败，error", str(e))

    orcl_conn.commit()
    end = time.time()
    orcl_cursor.close()
    orcl_conn.close()


def get_system_data():
    print("执行get_system_data")
    system_data={}
    # url_app = 'http://dev-pass.ehbapp.hubei.gov.cn:8050/hbzwAppServer/app/app/ok'#政务服务网域名
    url_app = 'http://192.168.77.160:8080/hbzwAppServer/app/app/ok'#内网IP
    data_text = requests.get(url_app)
    data1 = data_text.text
    # {"COMENUM": 124260, "DTIME": "03-21"}]
    #拼接当前日期
    localtime = time.localtime(time.time())
    print("localtime",localtime)
    # re_str = str(0)+str(localtime.tm_mon)+'-'+str(localtime.tm_mday)
    seconds_list=[]#多访问几次,添加到列表计算最大最小及平均值

    system_data['current_pv'] = 0#app暂时无法取数据为0
    system_data['current_uv'] = 0#app暂时无法取数据为0
    for _ in range(3):
        repose = requests.get(url_app)
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
    system_data['seqid'] = get_seq()
    system_data['url'] = url_app
    system_data['weburl'] = 'appburl'

    # 插入数据库中

    orcl_conn = oracle_connect()
    orcl_cursor = orcl_conn.cursor()
    logging.info("执行插入表:%s" % 'SERVICE_SYSTEM_APP')
    start = time.time()
    try:
        # 处理业务系统数据
        d = []
        d.append(system_data['current_uv'])
        d.append(system_data['current_pv'])
        d.append(system_data['reponse_time'])
        d.append(system_data['status_code'])
        d.append(system_data['reponse_max_time'])
        d.append(system_data['reponse_min_time'])
        d.append(system_data['reponse_avg_time'])
        d.append(system_data['url'])
        d.append(system_data['seqid'])
        d.append(system_data['weburl'])
        sql_system = "insert into SERVICE_SYSTEM_APP(CURUV,CURPV,RESPONSETIME,STATUSCODE,MAXTIME,MINITIME,AVGTIME,INTERFACEURL,SEQID,WEBURL) values (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10)"
        orcl_cursor.execute(sql_system, d)#执行sql语句
    except Exception as e:
        logging.error('插入数据库SERVICE_SYSTEM_APP报错error:%s' % str(e))
    # orcl_cursor.execute("insert into MID_DB_DATA(STATUS,MAXCONNS,CURCONNS,MIDDLEWARE_JVM,ID,SEQID) values " \
    # "('false','200','100','10%','3',SEQ_ID.NEXTVAL)")
    orcl_conn.commit()
    end = time.time()
    orcl_cursor.close()
    orcl_conn.close()
    logging.info("插入表%s共耗时%s秒" % ('SERVICE_SYSTEM_APP', end - start))







#远程执行命令
def python_ssh_command(ip, port, username, password,**shell):
    result = []
    try:
        print("开始执行命令%s"%shell)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())   # 用于允许连接不在known_hosts名单中的主机
        ssh.connect(ip, port, username, password,timeout=10)
        print("ssh",ssh)
        for key in shell:
            try:
                if 'nohup' in shell[key]:#解决掉执行nohup等一些java命令时会有等待命令输出导致程序始终保持等待状态
                # stdin,stdout,stderr = ssh.exec_command(shell[key])
                    stderr = ssh.exec_command(shell[key])
                    return
                stdin, stdout, stderr = ssh.exec_command(shell[key])
                channel = stdout.channel
                status = channel.recv_exit_status()
                print("status",status)
                if status==0:
                    print("已经连接到该主机%s:%s,%s:命令执行成功" %(ip,port,shell[key]))
                    #打印命令输出结果
                    #result['sccuss'] = (stdout.read().decode('utf-8'))#这种是全部取出来，但是有\n
                    for i in stdout.readlines():#这种是多行取一行，但是不有\n
                        print ("i",i)
                        result.append(i.rstrip())
                    # result['sccuss'] = stdout.readlines()[0].rstrip()#这种是多行取一行，但是不有\n
                else:
                    print("执行命令%s报错,请查看日志"% (shell[key]))
                    logging.error(str(stderr.read()))
                    print (stderr.read().decode('utf-8'))
            except Exception as e:
                print (stderr.read().decode('utf-8'),logging.error(str(e)))
            #stdin,stdout,stderr = ssh.exec_command(shell[key])
            #print("key",key)
        ssh.close()
        return result
    except Exception as e:
        print("ssh_commad have exception",str(e),logging.error(str(e)))
        return result
def midware_data():
    print("执行定时任务")
    data = []
    midware_ips = ['192.168.77.80','192.168.77.81','192.168.77.160','192.168.77.161','192.168.77.162','192.168.77.163','192.168.77.164','192.168.77.165','192.168.77.166'
        ,'192.168.77.167','192.168.77.168','192.168.77.169','192.168.77.170','192.168.77.171','192.168.77.172','192.168.77.173'
        ,'192.168.77.174','192.168.77.175','192.168.77.176','192.168.77.177','192.168.77.178','192.168.77.179'
        ,'192.168.77.112','192.168.77.113','192.168.77.114','192.168.77.210','192.168.77.211','192.168.77.212'
        ,'192.168.77.213','214']

    username = 'root'
    password = '1qaz@WSX'
    port = '22'
    for ip in midware_ips:
        midware_data = {}
        if ip == '192.168.77.112' or ip == '192.168.77.113' or ip == '192.168.77.114':  # 这里是fastdis,默认256个连接管理中间件
            username = 'root'
            password = 'zwfw2wsx#EDC'
            port = '22'
            midware_data['IP'] = ip
            result = python_ssh_command(ip, int(port), username, password,
                                        status='ps -ef|grep -v grep|grep fdfs |wc -l',
                                        curr='netstat -ant| grep 22122|grep EST|wc -l')
            midware_data['ID'] = '3'  # 3为中间件，4为数据库
            midware_data['MAXCONNS'] = '256'
            if len(result)>=1 and (result[0] != 0 or  result[0]!=[]):  # 不为0则连通状态为正常
                midware_data['STATUS'] = '1'
            else:
                midware_data['STATUS'] = '0'
            if len(result)>=2 and result[1]!=[]:#当前连接数
                midware_data['CURCONNS'] = result[1]
            else:
                midware_data['CURCONNS'] = str(0)
            midware_data['MIDDLEWARE_JVM'] = 'no jvm'
            midware_data['DBNULLSELECTTIME'] = 'null'
            midware_data['MIDDLEWARE_NAME'] = 'fastdfs'
            midware_data['SEQID'] = get_seq()
            data.append(midware_data)
        if ip == '192.168.77.210' or ip == '192.168.77.211' or ip == '192.168.77.212' or ip == '192.168.77.213':  # 这里是fastdis,默认256个连接管理中间件
            midware_data['IP'] = ip
            result = python_ssh_command(ip, int(port), username, password,
                                        status='ps -ef|grep -v grep|grep fdfs |wc -l',
                                        curr='netstat -ant| grep 23000|grep EST|wc -l')
            midware_data['ID'] = '3'  # 3为中间件，4为数据库
            midware_data['MAXCONNS'] = '256'
            if len(result)>=1 and (result[0] != 0 or  result[0]!=[]):  # 不为0则连通状态为正常
                midware_data['STATUS'] = '1'
            else:
                midware_data['STATUS'] = '0'
            if len(result)>=2 and result[1]!=[]:#当前连接数
                midware_data['CURCONNS'] = result[1]
            else:
                midware_data['CURCONNS'] = str(0)
            midware_data['MIDDLEWARE_JVM'] = 'no jvm'
            midware_data['DBNULLSELECTTIME'] = 'null'
            midware_data['MIDDLEWARE_NAME'] = 'fastdfs'
            midware_data['SEQID'] = get_seq()
            data.append(midware_data)
        if ip == '192.168.77.80' or ip == '192.168.77.81':  # 这里是nginx中间件
            username = 'root'
            password = 'yzw5tgb^YHN'
            port = '22'
            midware_data['IP'] = ip
            result = python_ssh_command(ip, int(port), username, password,
                                        status='ps -ef|grep -v grep|grep oracle |wc -l',
                                        curr="netstat -n | awk '/^tcp/ {++S[$NF]} END {for(a in S) print a,S[a]}'|grep EST|awk '{print $2}'")
            midware_data['ID'] = '3'  # 3为中间件，4为数据库
            midware_data['MAXCONNS'] = '65535'
            if len(result)>=1 and (result[0] != 0 or  result[0]!=[]):  # 不为0则连通状态为正常
                midware_data['STATUS'] = '1'
            else:
                midware_data['STATUS'] = '0'
            if len(result)>=2 and result[1]!=[]:#当前连接数
                midware_data['CURCONNS'] = result[1]
            else:
                midware_data['CURCONNS'] = '0'
            midware_data['MIDDLEWARE_JVM'] = 'no jvm'
            midware_data['DBNULLSELECTTIME'] = 'null'
            midware_data['MIDDLEWARE_NAME'] = 'nginx'
            midware_data['SEQID'] = get_seq()
            data.append(midware_data)
        if ip == '192.168.77.160' or ip == '192.168.77.161' or ip == '192.168.77.162' or ip == '192.168.77.163'\
                or ip == '192.168.77.164' or ip == '192.168.77.165' or ip == '192.168.77.166' or ip == '192.168.77.167'\
                or ip == '192.168.77.168' or ip == '192.168.77.169' or ip == '192.168.77.170' or ip == '192.168.77.171'\
                or ip == '192.168.77.172' or ip == '192.168.77.173' or ip == '192.168.77.174' or ip == '192.168.77.175'\
                or ip == '192.168.77.176' or ip == '192.168.77.177' or ip == '192.168.77.178' or ip == '192.168.77.179':  # 有jvm的，是jar中间件
            username = 'root'
            password = 'zwfw2wsx#EDC'
            port = '22'
            midware_data['IP'] = ip
            result = python_ssh_command(ip, int(port), username, password,
                                        status='ps -ef|grep -v grep|grep java |wc -l',
                                        curr='netstat -ant|grep 8080|grep EST|wc -l',
                                        jvm="/usr/java/jdk1.8.0_181/bin/jmap -heap `/usr/java/jdk1.8.0_181/bin/jps |grep Bootstrap|cut -d ' ' -f1`|grep -A4 'Eden Space'|grep '% used'|awk -F' ' '{print $1}'")
            midware_data['ID'] = '3'  # 3为中间件，4为数据库
            midware_data['MAXCONNS'] = '256'
            print("获取jvm",result)
            if len(result)>=1 and (result[0] != 0 or  result[0]!=[]):  # 不为0则连通状态为正常
                midware_data['STATUS'] = '1'
            else:
                midware_data['STATUS'] = '0'
            if len(result)>=2 and result[1]!=[]:
                midware_data['CURCONNS'] = result[1]
            else:
                midware_data['CURCONNS'] = '0'
            if len(result)>=3 and result[2]!=[]:
                midware_data['MIDDLEWARE_JVM'] = result[2]
            else:
                midware_data['MIDDLEWARE_JVM'] = '0'
            midware_data['MIDDLEWARE_NAME'] = 'jar'
            midware_data['SEQID'] = get_seq()
            data.append(midware_data)

        # 插入数据库中

    orcl_conn = oracle_connect()
    orcl_cursor = orcl_conn.cursor()
    logging.info("执行插入表:%s" % 'SERVICE_SYSTEM')
    start = time.time()
    try:
        # 处理业务系统数据
        #MIDDLEWARE_NAME,STATUS,MAXCONNS
        #sql_mid = "insert into MID_DB_DATA(MIDDLEWARE_NAME,STATUS,MAXCONNS,CURCONNS,MIDDLEWARE_JVM,ID,IP,SEQID) values (:1,:2,:3,:4,:5,:6,:7,:8)"
        sql_mid = "insert into MID_DB_APP(MIDDLEWARE_NAME,STATUS,MAXCONNS,CURCONNS,MIDDLEWARE_JVM,ID,IP,SEQID) values (:1,:2,:3,:4,:5,:6,:7,:8)"
        # sql_mid = 'select * from dual'
        for i in data:
            print("i",i)
            b = []
            b.append(i['MIDDLEWARE_NAME'])
            b.append(i['STATUS'])
            b.append(i['MAXCONNS'])
            b.append(i['CURCONNS'])
            b.append(i['MIDDLEWARE_JVM'])
            b.append(i['ID'])
            b.append(i['IP'])
            b.append(i['SEQID'])
            print("type",type(b),len(b),b)
            orcl_cursor.execute(sql_mid,b)
    except Exception as e:
        print("插入数据库报错error", str(e))
        logging.error('插入数据库MID_DB_DATA报错error:%s'%str(e))
    # orcl_cursor.execute("insert into MID_DB_DATA(STATUS,MAXCONNS,CURCONNS,MIDDLEWARE_JVM,ID,SEQID) values " \
    # "('false','200','100','10%','3',SEQ_ID.NEXTVAL)")
    orcl_conn.commit()
    end = time.time()
    orcl_cursor.close()
    orcl_conn.close()
    logging.info("插入表%s共耗时%s秒" % ('MID_DB_DATA', end - start))
    return data
if __name__ == '__main__':
    # #资源内部id,业务系统1，接口2，中间件3，数据库4

    c = midware_data()
    print("c",type(c),c)

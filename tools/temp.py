# -*- coding:utf-8 -*-


import datetime
import json
import re
import time

import logging

import os

import paramiko
import requests

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
    data = []

    midware_ips = [ '192.168.77.151']
    username = 'root'
    password = 'zwfw2wsx#EDC'
    port = '22'
    for ip in midware_ips:
        midware_data = {}
        midware_data['IP'] = ip
        result = python_ssh_command(ip, int(port), username, password,
                                    sql="sqlplus -S 'interface/interface12345678 as sysdba' << select to_char(sysdate,'yyyy-mm-dd') today from dual;exit;", curr='ps -ef|grep httpd|wc -l')
        # midware_data['ID'] = 3  # 3为中间件，4为数据库
        # data.append(midware_data)
        print("result",result)


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

if __name__=='__main__':
    b = [{'IP': '192.168.77.1', 'ID': '3', 'MAXCONNS': '2000', 'STATUS': '1', 'CURCONNS': '434', 'MIDDLEWARE_JVM': 'no jvm', 'DBNULLSELECTTIME': 'null', 'MIDDLEWARE_NAME': 'apache', 'SEQID': '202'}, {'IP': '192.168.77.2', 'ID': '3', 'MAXCONNS': '2000', 'STATUS': '1', 'CURCONNS': '481', 'MIDDLEWARE_JVM': 'no jvm', 'DBNULLSELECTTIME': 'null', 'MIDDLEWARE_NAME': 'apache', 'SEQID': '203'}, {'IP': '192.168.77.6', 'ID': '4', 'MAXCONNS': '1000', 'STATUS': '1', 'CURCONNS': '0', 'MIDDLEWARE_JVM': 'no jvm', 'DBNULLSELECTTIME': 'null', 'MIDDLEWARE_NAME': 'redis', 'SEQID': '204'}, {'IP': '192.168.77.20', 'ID': '4', 'MAXCONNS': '1000', 'STATUS': '1', 'CURCONNS': '0', 'MIDDLEWARE_JVM': 'no jvm', 'DBNULLSELECTTIME': 'null', 'MIDDLEWARE_NAME': 'redis', 'SEQID': '205'}, {'IP': '192.168.77.24', 'ID': '4', 'MAXCONNS': '1000', 'STATUS': '1', 'CURCONNS': '6', 'MIDDLEWARE_JVM': 'no jvm', 'DBNULLSELECTTIME': 'null', 'MIDDLEWARE_NAME': 'redis', 'SEQID': '206'}, {'IP': '192.168.77.26', 'ID': '3', 'MAXCONNS': '300', 'STATUS': '1', 'CURCONNS': '40', 'MIDDLEWARE_JVM': 'no jvm', 'DBNULLSELECTTIME': 'null', 'MIDDLEWARE_NAME': 'vsftp', 'SEQID': '207'}, {'IP': '192.168.77.27', 'ID': '3', 'MAXCONNS': '300', 'STATUS': '1', 'CURCONNS': '0', 'MIDDLEWARE_JVM': 'no jvm', 'DBNULLSELECTTIME': 'null', 'MIDDLEWARE_NAME': 'vsftp', 'SEQID': '208'}, {'IP': '192.168.77.32', 'ID': '4', 'MAXCONNS': '1500', 'STATUS': '1', 'CURCONNS': '313', 'MIDDLEWARE_JVM': 'no jvm', 'DBNULLSELECTTIME': 'null', 'MIDDLEWARE_NAME': 'oracle', 'SEQID': '209'}, {'IP': '192.168.77.33', 'ID': '4', 'MAXCONNS': '1500', 'STATUS': '1', 'CURCONNS': '183', 'MIDDLEWARE_JVM': 'no jvm', 'DBNULLSELECTTIME': 'null', 'MIDDLEWARE_NAME': 'oracle', 'SEQID': '210'}, {'IP': '192.168.77.16', 'ID': '3', 'MAXCONNS': '600', 'STATUS': '1', 'CURCONNS': '419', 'MIDDLEWARE_JVM': '0', 'MIDDLEWARE_NAME': 'tomcat', 'SEQID': '211'}, {'IP': '192.168.77.17', 'ID': '3', 'MAXCONNS': '600', 'STATUS': '1', 'CURCONNS': '448', 'MIDDLEWARE_JVM': '0', 'MIDDLEWARE_NAME': 'tomcat', 'SEQID': '212'}, {'IP': '192.168.77.18', 'ID': '3', 'MAXCONNS': '600', 'STATUS': '1', 'CURCONNS': '420', 'MIDDLEWARE_JVM': '0', 'MIDDLEWARE_NAME': 'tomcat', 'SEQID': '213'}, {'IP': '192.168.77.19', 'ID': '3', 'MAXCONNS': '600', 'STATUS': '1', 'CURCONNS': '443', 'MIDDLEWARE_JVM': '0', 'MIDDLEWARE_NAME': 'tomcat', 'SEQID': '214'}]
    orcl_conn = oracle_connect()
    orcl_cursor = orcl_conn.cursor()
    logging.info("执行插入表:%s" % 'SERVICE_SYSTEM')
    start = time.time()
    try:
        # 处理业务系统数据
        #MIDDLEWARE_NAME,STATUS,MAXCONNS
        #sql_mid = "insert into MID_DB_DATA(MIDDLEWARE_NAME,STATUS,MAXCONNS,CURCONNS,MIDDLEWARE_JVM,ID,IP,SEQID) values (:1,:2,:3,:4,:5,:6,:7,:8)"
        sql_mid = "insert into MID_DB_DATA(MIDDLEWARE_NAME,STATUS,MAXCONNS,CURCONNS,MIDDLEWARE_JVM,ID,IP,SEQID) values (:1,:2,:3,:4,:5,:6,:7,:8)"
        # sql_mid = 'select * from dual'
        for i in b:
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
        print("error",str(e))
    # orcl_cursor.execute("insert into MID_DB_DATA(STATUS,MAXCONNS,CURCONNS,MIDDLEWARE_JVM,ID,SEQID) values " \
    # "('false','200','100','10%','3',SEQ_ID.NEXTVAL)")


    c = {'current_uv': 4862, 'current_pv': 142780, 'reponse_time': 0.091522, 'status_code': 200, 'reponse_max_time': 100.6, 'reponse_min_time': 90.442, 'reponse_avg_time': 94.18799999999999, 'seqid': '280','url':'http://asdfsdf'}
    d = []
    d.append(c['current_uv'])
    d.append(c['current_pv'])
    d.append(c['reponse_time'])
    d.append(c['status_code'])
    d.append(c['reponse_max_time'])
    d.append(c['reponse_min_time'])
    d.append(c['reponse_avg_time'])
    d.append(c['url'])
    d.append(c['seqid'])
    sql_system = "insert into SERVICE_SYSTEM(CURUV,CURPV,RESPONSETIME,STATUSCODE,MAXTIME,MINITIME,AVGTIME,INTERFACEURL,SEQID) values (:1,:2,:3,:4,:5,:6,:7,:8,:9)"
    orcl_cursor.execute(sql_system, d)

    orcl_conn.commit()
    end = time.time()
    orcl_cursor.close()
    orcl_conn.close()
    logging.info("插入表%s共耗时%s秒" % ('SERVICE_SYSTEM', end - start))









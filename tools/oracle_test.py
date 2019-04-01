# -*- coding:utf-8 -*-
import datetime
import json
import re
import time

import logging

import os

import paramiko

def oracle_connect():
    import cx_Oracle
    # connection = cx_Oracle.connect("user", "password", "TNS")
    #host = '192.168.77.151'#内网IP
    host = '223.75.53.43'  # 外网IP
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
        orcl_cursor.execute('select seq_id.nextval from dual')
        seq_id = orcl_cursor.fetchall()
        return seq_id
    except Exception as e:
        print("error", str(e))
    # orcl_cursor.execute("insert into MID_DB_DATA(STATUS,MAXCONNS,CURCONNS,MIDDLEWARE_JVM,ID,SEQID) values " \
    # "('false','200','100','10%','3',SEQ_ID.NEXTVAL)")
    orcl_conn.commit()
    end = time.time()
    orcl_cursor.close()
    orcl_conn.close()
if __name__ == '__main__':
    c = get_seq()
    print(c)

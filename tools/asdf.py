#!/usr/bin/python
#--*--coding:utf-8--*--
from wsgiref.simple_server import make_server
import os
import pexpect
import logging
import sys
import paramiko



cmd='ssh root@192.168.77.159'
print("%s开始...." %cmd)
logging.info('%s开始' %cmd)
username='root'
password='zwfw2wsx#EDC'

try:
    process = pexpect.spawn(cmd)
    # logFileId = open(log_file, 'w')
    # process.logfile = logFileId
    index = process.expect(["Username for", 'Password for', "password:","\(yes\/no\)\?", pexpect.EOF, pexpect.TIMEOUT])
    print("index1",index,process.after)
    if index == 0:#git 命令
        process.sendline(username)
        index = process.expect(['Password for', 'Already',pexpect.EOF, pexpect.TIMEOUT])
        print("index2", index,process.after)
        process.sendline(password)
        # sendline("ls –l", cwd="/etc")#表示在/etc下执行ls -l
        process.read()
    elif index == 2:#scp命令
        print("index2", index, process.after)
        process.sendline(password)
        process.read()
    elif index==3:#ssh开始时输入yes/no
        print("index3",index,process.before)
        process.sendline('yes')#这里是scp命令
        index = process.expect(["password:", "Unknown host", pexpect.EOF, pexpect.TIMEOUT])
        if index == 0:
            process.sendline(password)
            process.read()
    else:
        print("Check the log for exceptions --%s" %cmd,logging.error(str(process.after)))
    print("%s结束...." % cmd)
    logging.info('命令结果%s' % process.after)
    logging.info('%s结束' % cmd)
except Exception as s:
    print("expect", str(s))
    logging.error(str(s))


#
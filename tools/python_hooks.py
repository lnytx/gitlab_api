#!/usr/bin/python
#--*--coding:utf-8--*--
from wsgiref.simple_server import make_server
import os
import pexpect
import logging
import sys
import paramiko
'''
代码需要从互联网提交，但是内网机器无法直接连互联网的IP，jenkins也无法绕过跳板机，只能通过在内网建立一个简单的web服务
通过互联网访问来触发代码提交
curl 192.168.77.151:8099/cty-gov/cty-userInfo/cty-dict/test
前面的IP换成外网访问，后面的test表示test环境(有多个环境，对应不同的IP)，前面则代表的是项目路径
'''
log_file = 'command.log'
logging.basicConfig(filename=log_file, level=logging.DEBUG,
                    format='[%(asctime)s] %(levelname)s [%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filemode='a')

def get_java(ip, user, passwd, cmd):#获取java环境变量路径
    ssh = pexpect.spawn('ssh %s@%s "%s"' % (user, ip, cmd))
    r = ''
    try:
        i = ssh.expect(['password: ', 'continue connecting (yes/no)?'])
        if i == 0 :
            ssh.sendline(passwd)
        elif i == 1:
            ssh.sendline('yes')
    except pexpect.EOF:
        ssh.close()
    else:
        r = ssh.read()
        ssh.expect(pexpect.EOF)
        ssh.close()
    return (r.decode().lstrip()).rstrip()

#自动交互
def pexpect_command(cmd,ip,username,password,project_name,project_src):
    print("%s开始...." %cmd)
    logging.info('%s开始' %cmd)
    try:
        process = pexpect.spawn(cmd,cwd=project_src)
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

 #远程执行命令
def python_ssh_command(ip, port, username, password,**shell):
    result = {}
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
                    #print (stdout.read().decode('utf-8'))
                else:
                    print("执行命令%s报错,请查看日志"% (shell[key]))
                    logging.error(str(stderr.read()))
                    print (stderr.read().decode('utf-8'))
            except Exception as e:
                print (stderr.read().decode('utf-8'),logging.error(str(e)))
            #stdin,stdout,stderr = ssh.exec_command(shell[key])
            #print("key",key)
            result[key] = stdout.read().decode('utf-8'),stderr.read().decode('utf-8')
        ssh.close()
        print("result",result,type(result))
        return result
    except Exception as e:
        print("ssh_commad have exception",str(e),logging.error(str(e)))
        return result



# if __name__=='__main__':
#     # s=b'\xe6\x89\xa7\xe8\xa1\x8c\xe7\xbb\x93\xe6\x9e\x9c'
#     # print(s.decode('utf-8'))
#
#
#     httpd = make_server('', 8099, application)  # 监听8009端口
#     print('Serving HTTP on port 8009...')#启动一个简单的web服务
#     httpd.serve_forever()



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


#自动交互
def pexpect_command(cmd,ip,username,password,project_name,project_src):
    print("%s开始...." %cmd)
    logging.info('%s开始' %cmd)
    try:
        process = pexpect.spawn(cmd,cwd=project_src,logfile=sys.stdout)
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
def application(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    master_ip='192.168.77.151'
    port = '22'
    username = ['root', 'root']  # 0为主机用户，1为gitlab用户
    password = ['zwfw2wsx#EDC', 'rootroot']  # 0为主机密码，1为gitlab密码
    src='/data/projects'#项目所在路径，脚本文件放入此目录中
    #target = '/data/robert/app'#要分发的目标机器路径,存放jar包的目录
    target = '/data/test'
    JAVA_HOME = '/opt/jdk1.8.0_171/bin/java'
    #os.system('cd /soft ； touch aaa.txt') # 切换到项目的目录，并且执行pull操作
    pathDirs = environ['PATH_INFO'].split('/')#获取前台传入值
    tmp = [x for x in pathDirs if x != '']
    if ''.join(tmp[-1]).lower()=='test':
        ips = ['192.168.77.154']
    elif  ''.join(tmp[-1]).lower()=='pro':
        ips=[]
    elif ''.join(tmp[-1]).lower()=='dev':
        ips=[]
    else:
        return '<h1>deploy command  %s is not error[test,pro,dev]</h1>' % (''.join(tmp[-1]))
    project_name=''
    project_name=tmp[0]# 获取前台传入的大的项目名称
    if len(tmp)>1:
        sub_project_name = '/'.join(tmp[i] for i in range(1, len(tmp)-1))  # 获取小的项目名称
    else:
        sub_project_name=project_name
    print("project_name",project_name)
    print("sub_project_name",sub_project_name)
    cmds=['git pull','scp','git clone']
    pathDir = os.listdir(os.getcwd())#先检查当前目录是否存在项目，
    print("pathDir",pathDir)
    if project_name in pathDir:
        logging.info(str(project_name) + '已存在')
        cmd=cmds[0]
        project_src = os.path.join(os.path.join(os.getcwd(), src),project_name)
        #有项目就先git pull
        pexpect_command(cmd, master_ip, username[1], password[1], project_name, project_src)
        logging.info("git pull:%s" % cmd)
    else:#无项目就clone
        cmd='git clone http://192.168.77.151:8084/root/%s.git'%project_name
        logging.info("git clone:%s"%cmd)
        project_src = os.getcwd()
        pexpect_command(cmd, master_ip, username[1], password[1], project_name, project_src)
    # 然后推送
    project_src = os.path.join(os.path.join(os.getcwd(), src), project_name)#重新设置project_src的值
    sub_project = os.path.join(project_src, sub_project_name)  # 获取小项目路径
    if not os.path.isdir(sub_project):
        return '<h1>deploy error %s is not exists</h1>' % (sub_project_name)
    print("sub_proect path", sub_project)
    # maven打包，然后推送打包sub项目
    os.system('cd %s;mvn clean install -Dmaven.test.skip=true' % project_src)
    os.system('cd %s;mvn clean package' % sub_project)  # 打包小项目
    # mvn clean package[前台可以传{'project_name':'sss','mvn':'dssss']
    if sub_project_name != '':
        target_jar = os.path.join(sub_project, 'target/%s.jar' % ''.join(tmp[-2]))
    else:
        target_jar = os.path.join(sub_project, 'project_name/%s.jar' % project_name)
    print("target_jar", target_jar)
    for ip in ips:
        # 要在对应的机器上先kill掉之前的进程，然后scp过去之后再启动
        cmd = "ps -ef|grep %s.jar|grep -v grep|awk '{print $2}'|xargs -i kill {}" % ''.join(tmp[-2])
        logging.info("杀掉进程:%s" % cmd)
        python_ssh_command(ip, int(port), username[0], password[0], a='cd %s && %s' % (target, cmd))
        cmd = 'scp -P %s -r %s %s@%s:%s' % (port, target_jar, username[0], ip, target)
        logging.info("scp jar包:%s" % cmd)
        pexpect_command(cmd, ip, username[0], password[0], project_name, project_src)
        cmd = 'cd %s && nohup %s -jar %s.jar --spring.profiles.active=%s>/dev/null 1>&2 &' % \
              ( target,JAVA_HOME, ''.join(tmp[-2]),''.join(tmp[-1]).lower())
        logging.info("启动 jar包:%s" % cmd)
        python_ssh_command(ip, int(port), username[0], password[0], args='%s' % cmd)
    return '<h1>deploy %s</h1>' % (environ['PATH_INFO'][1:])


# if __name__=='__main__':
#     # s=b'\xe6\x89\xa7\xe8\xa1\x8c\xe7\xbb\x93\xe6\x9e\x9c'
#     # print(s.decode('utf-8'))
#
#
#     httpd = make_server('', 8099, application)  # 监听8009端口
#     print('Serving HTTP on port 8009...')#启动一个简单的web服务
#     httpd.serve_forever()



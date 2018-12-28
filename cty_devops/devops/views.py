import logging
import os
from datetime import datetime, timedelta

from django.http import response, HttpResponse, JsonResponse
from django.shortcuts import render, render_to_response

import requests
import json

# Create your views here.
from tools.python_hooks import pexpect_command, python_ssh_command


def test(request):
    return render(request, 'index.html')

def gitlab_commit(request):
    '''
    获取当前项目的提交信息
    '''
    private_token = 'x_aXP2ZJV89b2q3dWsRw'
    url3 = 'http://223.75.53.43:8084/api/v4/projects/17/repository/commits?private_token=%s&per_page=50' % private_token
    r = requests.get(url3)
    data = r.text
    print("data1", type(data), data)
    a = json.loads(data)
    print("data", type(a), len(a), a)
    my_project = []
    result={}
    msg = []
    if isinstance(a, dict):
        for k, v in a.items():
            print(k, v)
            if 'test' == v:  # 按项目名称取自己的项目
                my_project.append(v)
                print("我自己的项目", my_project)
                break
    elif isinstance(a, list):
        for item in a:
            result={}
            result['committer_name'] = item['committer_name']
            result['committed_date'] = (datetime.strptime(item['committed_date'],"%Y-%m-%dT%H:%M:%S.%fZ")+timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
            result['message'] = item['message']
            msg.append(result)


    #正式的推送功能
    log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),'logs\command.log')
    print("logfile",log_file)
    logging.basicConfig(filename=log_file, level=logging.DEBUG,
                        format='[%(asctime)s] %(levelname)s [%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        filemode='a')
    master_ip = '192.168.77.151'
    port = '22'
    username = ['root', 'root']  # 0为主机用户，1为gitlab用户
    password = ['zwfw2wsx#EDC', 'rootroot']  # 0为主机密码，1为gitlab密码
    src = '/data/projects'  # 项目所在路径，脚本文件放入此目录中
    # target = '/data/robert/app'#要分发的目标机器路径,存放jar包的目录
    target = '/data/test'
    JAVA_HOME = '/opt/jdk1.8.0_171/bin/java'
    # os.system('cd /soft ； touch aaa.txt') # 切换到项目的目录，并且执行pull操作
    pathDirs = request.path.split('/')  # 获取前台传入的不带参数的项目路径
    tmp = [x for x in pathDirs if x != '']
    if ''.join(tmp[-1]).lower() == 'test':
        ips = ['192.168.77.154']
    elif ''.join(tmp[-1]).lower() == 'pro':
        ips = []
    elif ''.join(tmp[-1]).lower() == 'dev':
        ips = []
    else:
        status={'msg':"错误的命令，路径最后应该要指明需要提交的环境，当前最后一条命令是:%s"%''.join(tmp[-1])}
        return render(request, 'index.html', {'status':status})
        # return HttpResponse("错误的命令，路径最后应该要指明需要提交的环境:%s"%''.join(tmp[-1]))
    project_name = ''
    project_name = tmp[0]  # 获取前台传入的大的项目名称
    if len(tmp) > 1:
        sub_project_name = '/'.join(tmp[i] for i in range(1, len(tmp) - 1))  # 获取小的项目名称
    else:
        sub_project_name = project_name
    print("project_name", project_name)
    print("sub_project_name", sub_project_name)
    cmds = ['git pull', 'scp', 'git clone']
    pathDir = os.listdir(os.getcwd())  # 先检查当前目录是否存在项目，
    print("pathDir", pathDir)
    if project_name in pathDir:
        logging.info(str(project_name) + '已存在')
        cmd = cmds[0]
        project_src = os.path.join(os.path.join(os.getcwd(), src), project_name)
        # 有项目就先git pull
        pexpect_command(cmd, master_ip, username[1], password[1], project_name, project_src)
        logging.info("git pull:%s" % cmd)
    else:  # 无项目就clone
        cmd = 'git clone http://192.168.77.151:8084/root/%s.git' % project_name
        logging.info("git clone:%s" % cmd)
        project_src = os.getcwd()
        pexpect_command(cmd, master_ip, username[1], password[1], project_name, project_src)
    # 然后推送
    project_src = os.path.join(os.path.join(os.getcwd(), src), project_name)  # 重新设置project_src的值
    sub_project = os.path.join(project_src, sub_project_name)  # 获取小项目路径
    if not os.path.isdir(sub_project):
        status={'msg':"%s不存的项目路径，请检查后重试"%sub_project_name}
        return render(request, 'index.html', {'status': status})
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
              (target, JAVA_HOME, ''.join(tmp[-2]), ''.join(tmp[-1]).lower())
        logging.info("启动 jar包:%s" % cmd)
        python_ssh_command(ip, int(port), username[0], password[0], args='%s' % cmd)
    status={'sccuss':'提交成功'}
    return render(request,'index.html', {'result':msg,'status':status})
    # return HttpResponse(json.dumps(msg,ensure_ascii=False), content_type="application/json,charset=utf-8")

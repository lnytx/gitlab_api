import logging
import os
from datetime import datetime, timedelta

from django.http import HttpResponse
from django.shortcuts import render

import requests
import json

# Create your views here.
from python_hooks import python_ssh_command, pexpect_command


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
    a = json.loads(data)
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
    # 获取前台传递的数据
    if request.is_ajax():
        if 'button_text' in request.GET:
            button_deploy = request.GET.get('button_text')
            print("选中的按钮值",button_deploy)
        if 'nodes_name' in request.GET:
            nodes_name = request.GET.get('nodes_name')
            print("选中要提交的目录",nodes_name)
    project_names = request.path.split('/')
    tmp = [x for x in project_names if x != '']
    project_name = tmp[0]#实际中的项目名称

    print("从path中获取project_name",project_name)
    pathDirs = nodes_name.split(',')  # 获取前台传入的不带参数的项目路径
    print("pathDirs",pathDirs)
    # sub_projects = ['gov_cty/'+x for x in pathDirs]
    sub_projects=pathDirs
    if nodes_name[0] == project_name:  # 这里判断该项目是否有子项目，名称相同则表示没有子项目
        sub_projects = []
        sub_projects[0] = project_name
    print("sub_projects",type(sub_projects),sub_projects)
    if button_deploy == 'test':
        ips = ['192.168.77.154']
    elif ''.join(tmp[-1]).lower() == 'pro':
        ips = []
    elif ''.join(tmp[-1]).lower() == 'dev':
        ips = []
    cmds = ['git pull', 'scp', 'git clone']
    server_pathDir = os.listdir(src)  # 先检查当前目录是否存在项目，
    print("pathDir", server_pathDir)
    print("project_name",project_name)
    sub_project_name=1
    if project_name in server_pathDir:
        logging.info(str(project_name) + '已存在')
        cmd = cmds[0]
        project_src = os.path.join(src, project_name)
        # 有项目就先git pull
        pexpect_command(cmd, master_ip, username[1], password[1], project_name, project_src)
        logging.info("git pull:%s" % cmd)
    else:  # 无项目就clone
        cmd = 'git clone http://192.168.77.151:8084/root/%s.git' % project_name
        logging.info("git clone:%s" % cmd)
        project_src = src
        pexpect_command(cmd, master_ip, username[1], password[1], project_name, project_src)
        # 然后就逐个小项目去推送
    for item in sub_projects:
        print("item",item)
        project_src = os.path.join(src, project_name)  # 重新设置project_src的值
        sub_project = os.path.join(project_src, item)  # 获取小项目路径
        if not os.path.isdir(sub_project):
            status={"code":-1,'msg':"%s不存的项目路径，请检查后重试"%sub_project_name}
            return render(request, 'test.html', {'status': status})
        print("sub_proect path", sub_project)
        # maven打包，然后推送打包sub项目
        os.system('cd %s;mvn clean install -Dmaven.test.skip=true' % project_src)
        os.system('cd %s;mvn clean package' % sub_project)  # 打包小项目
        # mvn clean package[前台可以传{'project_name':'sss','mvn':'dssss']
        target_jar = os.path.join(sub_project, 'target/%s.jar' % item)
        print("target_jar", target_jar)
        for ip in ips:
            # 要在对应的机器上先kill掉之前的进程，然后scp过去之后再启动
            cmd = "ps -ef|grep %s.jar|grep -v grep|awk '{print $2}'|xargs -i kill {}" % item
            logging.info("杀掉进程:%s" % cmd)
            python_ssh_command(ip, int(port), username[0], password[0], a='cd %s && %s' % (target, cmd))
            cmd = 'scp -P %s -r %s %s@%s:%s' % (port, target_jar, username[0], ip, target)
            logging.info("scp jar包:%s" % cmd)
            pexpect_command(cmd, ip, username[0], password[0], project_name, project_src)
            cmd = 'cd %s && nohup %s -jar %s.jar --spring.profiles.active=%s -Duser.timezone=GMT+08>/dev/null 1>&2 &' % \
                  (target, JAVA_HOME, item, button_deploy)
            logging.info("启动 jar包:%s" % cmd)
            python_ssh_command(ip, int(port), username[0], password[0], args='%s' % cmd)
        status={'sccuss':'提交成功'}
        return render(request,'aaa/test.html', {'result':msg,'status':status})
        # return HttpResponse(json.dumps(msg,ensure_ascii=False), content_type="application/json,charset=utf-8")

def test1(request):
    status = {'sccuss': '提交成功'}
    return render(request, 'aaa/test.html', { 'status': status})
def ddd(request):
    private_token = 'x_aXP2ZJV89b2q3dWsRw'
    #url3 = 'http://223.75.53.43:8084/api/v4/projects/17/repository/tree/?path=cty-config&private_token=%s&per_page=50' % private_token
    url3 = 'http://223.75.53.43:8084/api/v4/projects/17/repository/tree/?private_token=%s&per_page=50' % private_token
    r = requests.get(url3)
    data = r.text
    a = json.loads(data)
    print("父节点",a)
    return HttpResponse(json.dumps(a), content_type="application/json")

def aaa(request):
    if request.is_ajax():
        if 'text' in request.GET:
            parent_dir = request.GET.get('text')
            print("父级目录",parent_dir)
    private_token = 'x_aXP2ZJV89b2q3dWsRw'
    #url3 = 'http://223.75.53.43:8084/api/v4/projects/17/repository/tree/?path=cty-config&private_token=%s&per_page=50' % private_token
    url3 = 'http://223.75.53.43:8084/api/v4/projects/17/repository/tree/?path=%s&private_token=%s&per_page=50' % (parent_dir,private_token)
    r = requests.get(url3)
    data = r.text
    a = json.loads(data)
    print("子级目录", type(a), len(a),a)
    print("子级目录",type(json.dumps(a)),json.dumps(a))
    return HttpResponse(json.dumps(a), content_type="application/json")
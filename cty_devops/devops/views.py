import logging
import os
import re
from datetime import datetime, timedelta

from django.http import HttpResponse
from django.shortcuts import render

import requests
import json

# Create your views here.
from python_hooks import python_ssh_command, pexpect_command


def index(request):
    return render(request, 'test.html')

def gitlab_commit(request):
    '''
    获取当前项目的提交信息
    '''
    private_token = 'x_aXP2ZJV89b2q3dWsRw'
    project_name = request.path
    print("project_name", type(project_name), project_name)
    curent_project_name = project_name[1:project_name.index('/', 1)]#获取request中的当前项目名称
    print("curent_project_name",curent_project_name)
    url = 'http://223.75.53.43:8084/api/v4/projects?private_token=%s&search=%s' % ( private_token, curent_project_name)  # 获取指定项目信息，根据项目名称获取项目id
    r = requests.get(url)
    data = r.text
    a = json.loads(data)
    project_id = a[0]['id']#根据项目名称获取项目id
    url3 = 'http://223.75.53.43:8084/api/v4/projects/%s/repository/commits?private_token=%s&per_page=10' % (project_id,private_token)
    r = requests.get(url3)
    data = r.text
    a = json.loads(data)
    print("提交详情",type(a),a)
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
    print("msg",msg)


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
    src = '/data/projects/projects2'  # 项目所在路径，脚本文件放入此目录中
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

    print("从path中获取project_name",project_name)
    pathDirs = nodes_name.split(',')  # 获取前台传入的不带参数的项目路径
    print("pathDirs",len(pathDirs),pathDirs[0],pathDirs)
    sub_projects = [curent_project_name+x for x in pathDirs]
    print("子项目",sub_projects)
    if len(pathDirs)==1 and pathDirs[0] == curent_project_name:  # 这里判断该项目是否有子项目，名称相同则表示没有子项目，相当是重置上面的子项目
        sub_projects = []
        sub_projects = pathDirs
    print("sub_projects",type(sub_projects),sub_projects)
    if button_deploy == 'test':
        ips = ['192.168.77.155']
    elif button_deploy == 'pro':
        ips = []
    elif button_deploy == 'dev':
        ips = []
    cmds = ['git pull', 'scp', 'git clone']
    server_pathDir = os.listdir(src)  # 先检查当前目录是否存在项目，
    print("pathDir", server_pathDir)
    print("project_name",curent_project_name)
    sub_project_name=1
    if curent_project_name in server_pathDir:
        logging.info(str(curent_project_name) + '已存在')
        cmd = cmds[0]
        project_src = os.path.join(src, curent_project_name)
        # 有项目就先git pull
        pexpect_command(cmd, master_ip, username[1], password[1], project_name, project_src)
        logging.info("git pull:%s" % cmd)
    else:  # 无项目就clone
        cmd = 'git clone http://192.168.77.151:8084/root/%s.git' % curent_project_name
        logging.info("git clone:%s" % cmd)
        project_src = src#没有对应的项目时src为项目初始路径
        pexpect_command(cmd, master_ip, username[1], password[1], curent_project_name, project_src)
        # 然后就逐个小项目去推送
    for item in sub_projects:
        print("item",item)
        project_src = os.path.join(src, curent_project_name)  # 重新设置project_src的值,这里是大项目所在的路径
        sub_project = os.path.join(src, item)  # 获取小项目路径
        print("子项目的绝对路径",sub_project)
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
        return render(request,'aaa/ztree_test.html', {'result':msg,'status':status})
        # return HttpResponse(json.dumps(msg,ensure_ascii=False), content_type="application/json,charset=utf-8")

def get_nodes(request):
    private_token = 'x_aXP2ZJV89b2q3dWsRw'
    if request.is_ajax():
        if 'project' in request.GET:#获取项目顶级目录
            project_name = request.path
            print("project_name", type(project_name), project_name)
            curent_dir = project_name[1:project_name.index('/', 1)]
            print("result", curent_dir)
            url = 'http://223.75.53.43:8084/api/v4/projects?private_token=%s&search=%s' % (private_token, curent_dir)  # 获取指定项目信息
            r = requests.get(url)
            data = r.text
            a = json.loads(data)
            project_id = a[0]['id']
            project_name = a[0]['name']
            print("项目id为", project_id)
            print("父节点", type(a), len(a), a)
            temp = {}
            ret = []
            temp['id'] = project_id
            temp['text'] = project_name
            ret.append(temp)
            return HttpResponse(json.dumps(ret), content_type="application/json")
        if 'selectedNode_text' in request.GET:#获取项目次级目录
            project_name = request.path
            print("project_name", type(project_name), project_name)
            temp = project_name[1:project_name.index('/', 1)]
            print("result", temp)
            url = 'http://223.75.53.43:8084/api/v4/projects?private_token=%s&search=%s' % (
            private_token, temp)  # 获取指定项目信息
            r = requests.get(url)
            data = r.text
            a = json.loads(data)
            project_id = a[0]['id']
            temp = project_name[1:project_name.index('/', 1)]
            print("项目名称", temp)
            curent_dir = request.GET.get('selectedNode_text')
            print("父级目录",curent_dir)
            print("project_name",project_name)
            # url3 = 'http://223.75.53.43:8084/api/v4/projects/17/repository/tree/?path=cty-config&private_token=%s&per_page=50' % private_token
            if curent_dir == temp:  # 如果点击的是顶级目录
                print("parent_dir",curent_dir)
                url = 'http://223.75.53.43:8084/api/v4/projects/%s/repository/tree/?private_token=%s' % ( project_id, private_token)  # 获取所有项目二级目录(项目名为1级)
                #url = 'http://223.75.53.43:8084/api/v4/projects/17/repository/tree/?path=%s&private_token=%s' % ( parent_dir, private_token)
                #url = 'http://223.75.53.43:8084/api/v4/projects?private_token=%s&search=%s' % (private_token, parent_dir)  # 获取指定项目信息
                r = requests.get(url)
                data = r.text
                a = json.loads(data)
                print("a", type(a), a)
                data = []
                for item in a:
                    print("item", type(item), item)
                    temp = {}
                    if item['type'] != 'tree':
                        temp['icon'] = 'jstree-file'
                        temp["state"] = { "disabled": 'true' }
                    # if item['type'] == 'tree':
                    temp['id'] = item['id']
                    temp['text'] = item['path']
                    data.append(temp)
                print("data", data)
                return HttpResponse(json.dumps(data), content_type="application/json")
            else:#获取三级目录
                curent_dir = request.GET.get('selectedNode_text')
                parent_dir = request.GET.get('parent_text')#获取父级目录
                print("parent_dir三",curent_dir)
                print("project_id三",project_id)
                url = 'http://223.75.53.43:8084/api/v4/projects/%s/repository/tree/?path=%s&private_token=%s' % (project_id,curent_dir, private_token)
                r = requests.get(url)
                data = r.text
                a = json.loads(data)
                print("a", type(a), a)
                data = []
                for item in a:
                    print("item", type(item), item)
                    temp = {}
                    if item['type'] != 'tree':#针对的是文件类型
                        temp['icon'] = 'jstree-file'
                        temp["state"] = {"disabled": 'true'}
                    temp['id'] = item['id']
                    temp['text'] = item['path']
                    data.append(temp)
                print("data", data)
                return HttpResponse(json.dumps(data), content_type="application/json")

    #url = 'http://223.75.53.43:8084/api/v4/projects/%s/repository/tree/?private_token=%s' % ( project_id, private_token)  # 获取所有项目二级目录(项目名为1级)




def cty_gov(request):
    project_name = request.path
    print("project_name", type(project_name), project_name)
    result = project_name[1:project_name.index('/', 1)]
    print("result", result)
    data = []
    temp = {}
    temp['id'] = '123123'
    temp['text'] = result
    data.append(temp)
    print("data", data)
    return render(request, 'aaa/ztree_test.html')
    # return HttpResponse(json.dumps(data), content_type="application/json")


#-*- codeing=utf8 -*-
#!/usr/bin/env python
import json
import os

import requests

def test():
    private_token = 'x_aXP2ZJV89b2q3dWsRw'
    master_ip='223.75.53.43'
    curent_dir='cty-flagShipstore'
    url = 'http://%s:8084/api/v4/projects/%s/repository/tree/?path=%s&private_token=%s' % (
    master_ip, curent_dir, curent_dir, private_token)

    url = 'http://%s:8084/api/v4/projects?private_token=%s&search=%s' % (master_ip, private_token, curent_dir)  # 获取指定项目信息
    r = requests.get(url)
    data = r.text
    a = json.loads(data)
    print('a',a)
    project_id = a[0]['id']
    project_name = a[0]['name']
    temp = {}
    ret = []
    temp['id'] = project_id
    temp['text'] = project_name
    ret.append(temp)
def test2():
    private_token = 'x_aXP2ZJV89b2q3dWsRw'
    master_ip = '223.75.53.43'
    project_id = 24
    curent_dir = 'cty-store'
    url = 'http://%s:8084/api/v4/projects?private_token=%s&search=%s' % (master_ip, private_token, curent_dir)  # 获取指定项目信息
    #url = 'http://%s:8084/api/v4/projects?private_token=%s&search=%s' % (master_ip, private_token, project_id)  # 获取指定项目信息
    #url = 'http://%s:8084/api/v4/projects/%s/repository/tree/?private_token=%s' % (
    #master_ip, project_id, private_token)  # 获取所有项目二级目录(项目名为1级)
    r = requests.get(url)
    data = r.text
    a = json.loads(data)
    temp=[]
    for i in a:
        temp.append(i['name'])
        if 'pom.xml' in temp:
            print("这是一个maven项目")
        # if i['name']=='pom.xml':
        #     print(i)
        #     print ("这是一个maven项目")
    print (temp)
if __name__=='__main__':
    # rc = test()
    a='/data/projects'
    b='asf'
    print(os.path.join(a,b).replace('\\','/'))
    # rc = test2()

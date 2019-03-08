#-*- codeing=utf8 -*-
#!/usr/bin/env python
import json

import requests

def test():
    private_token = 'x_aXP2ZJV89b2q3dWsRw'
    master_ip='223.75.53.43'
    curent_dir='cty-gov'
    url = 'http://%s:8084/api/v4/projects?private_token=%s&search=%s' % (master_ip,private_token, curent_dir)  # 获取指定项目信息
    r = requests.get(url)
    data = r.text
    a = json.loads(data)
    project_id = a[0]['id']
    project_name = a[0]['name']
    temp = {}
    ret = []
    temp['id'] = project_id
    temp['text'] = project_name
    ret.append(temp)
if __name__=='__main__':
    rc = test()

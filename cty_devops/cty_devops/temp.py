import json

import requests

def aaa():
    private_token = 'x_aXP2ZJV89b2q3dWsRw'
    url3 = 'http://223.75.53.43:8084/api/v4/projects/17/repository/tree/?path=cty-config&private_token=%s&per_page=50' % private_token
    r = requests.get(url3)
    data = r.text
    a = json.loads(data)
    print("a",type(a),a)
    my_project = []
    result = {}
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
            pass
if __name__=='__main__':
    x = 3
    y = 8
    a=++x*y
    print("a",a)
    print(++x*y)

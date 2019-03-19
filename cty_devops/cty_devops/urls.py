"""cty_devops URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import url
from devops import views as cty_devops



urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^index/$', cty_devops.index,name='index'),
    # url(r'^gitlab/$', cty_devops.gitlab_commit,name='gitlab_commit'),
    # url(r'^cty-gov/*', cty_devops.gitlab_commit,name='gitlab_commit'),
    # url(r'^test_gov/*', cty_devops.gitlab_commit,name='gitlab_commit'),

    # url(r'^cty-storeBackstage/$', cty_devops.storeBackstage, name='storeBackstage'),

    # url(r'^cty-store/$', cty_devops.cty_gov, name='cty_gov'),
    # url(r'^cty-store/get_nodes/$', cty_devops.get_nodes, name='get_nodes'),
    # url(r'cty-store/project/', cty_devops.get_nodes, name='get_parents_nodes'),
    # url(r'cty-store/gitlab_commit/', cty_devops.gitlab_commit, name='gitlab_commit'),

    url(r'cty-[a-zA-Z]{3,16}/$', cty_devops.cty_gov,name='cty_gov'),
    url(r'cty-[a-zA-Z]{3,16}/get_nodes/$', cty_devops.get_nodes,name='get_nodes'),
    url(r'cty-[a-zA-Z]{3,16}/project/$', cty_devops.get_nodes,name='get_parents_nodes'),
    url(r'cty-[a-zA-Z]{3,6}/gitlab_commit/$', cty_devops.gitlab_commit,name='gitlab_commit'),
    # 非maven项目提交
    url(r'^cty-flagshipStore/gitlab_commit_notmvn/$', cty_devops.gitlab_commit_notmvn, name='gitlab_commit_notmvn'),

    #需要使用npm项目打包的
    url(r'^cty-storeBackstage/gitlab_commit_npm/$', cty_devops.gitlab_commit_npm, name='gitlab_commit_notmvn'),








]

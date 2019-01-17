#!/usr/bin/env python
# -*- coding=utf-8 -*-

# leaning ansbile api ing~

import json, sys, os
import logging
from ansible import constants
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from ansible.inventory.host import Host, Group
from ansible.plugins.callback import CallbackBase
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.executor.playbook_executor import PlaybookExecutor


class MyInventory():

    '''
    resource = [{'hostid': '1231', 'hostname': 'h1', 'hostip': '1.1.1.1'},
                {'hostid': '2345', 'hostname': 'h2', 'hostip': '2.2.2.2'},
                ]
    resource = {'groupname1': {
        'hosts': [
            {'hostid': '1231', 'hostname': 'h1', 'hostip': '1.1.1.1'},
            {'hostid': '2231', 'hostname': 'h2', 'hostip': '1.1.1.2'},
                 ],
        'groupvars': {"k1":"v1"}
                              },
                'groupname2': {'hosts': [], 'groupvars': {}},
                              }
    '''

    # edit ori code  ansible/inventory/manage.pay line215  try if C.InventoryManager_PARSE_NOSOURCE:pass
    constants.InventoryManager_PARSE_NOSOURCE=True
    def __init__(self,resource):
        self.resource=resource
        self.loader=DataLoader()
        # self.inventory=InventoryManager(loader=self.loader,sources=['/etc/ansible/hosts'])
        self.inventory=InventoryManager(loader=self.loader)
        self.variable_manager=VariableManager(loader=self.loader,inventory=self.inventory)
        self._parse(self.resource)

    def _parse(self,resource):
        if isinstance(resource,list):
            self._addGroupHosts(self.resource)
        elif isinstance(resource,dict):
            # logging.info('parsing resuorce: %s'%(self.resource))
            for groupname,hosts_and_groupvars in self.resource.items():
                print("[1] groupname: %s |hostsandvars: %s"%(groupname,hosts_and_groupvars))                                                    # debug [1]
                self._addGroupHosts(hosts_and_groupvars.get('hosts'),groupname,hosts_and_groupvars.get('groupvars'))

        else:
            logging.error('resource error ,need dict or list')

    def _addGroupHosts(self,hosts,groupname='default',groupvars=None):
        self.inventory.add_group(group=groupname)
        group=Group(groupname)
        if groupvars:
            for k,v in groupvars.items():
                group.set_variable(k,v)

        # hosts=[{'hostid':'123','hostname':'h1','hostip':'192.168.188.20'}
        for host in hosts:
            hostid=host.get('hostid')
            hostname=host.get('hostname')
            hostip=host.get('hostip')
            username=host.get('username')
            password=host.get('password')
            port=host.get('port',22)
            sshkey=host.get('sshkey')
            if hostname:
                self.inventory.add_host(host=hostname,group=groupname)   # by default, indentify by hostname and need
                hostobj= self.inventory.get_host(hostname=hostname)     # add host= , get hostname=

                self.variable_manager.set_host_variable(host=hostobj,varname='ansible_ssh_host',value=hostip)
                self.variable_manager.set_host_variable(host=hostobj,varname='ansible_ssh_port',value=port)
                self.variable_manager.set_host_variable(host=hostobj,varname='ansible_ssh_user',value=username)
                self.variable_manager.set_host_variable(host=hostobj,varname='ansible_ssh_pass',value=password)
                self.variable_manager.set_host_variable(host=hostobj,varname='ansible_ssh_private_key_file',value=sshkey)

                # TODO: other vars such as become-method-user-pass
                #hostobj.set_variable('ansible_ssh_port',port)
                for k,v in host.items():
                    if k not in ['hostip','port','username','password','sshkey']:
                        hostobj.set_variable(k,v)
            else:
                logging.warning('resource error:cant get hostname from | %s'%resource)

    def testcase(self):
        print(self.inventory.get_groups_dict())
        host=self.inventory.get_host(hostname='h1')
        print(self.variable_manager.get_vars(host=host))


class ADhocCallback(CallbackBase):
    def __init__(self, *args, **kwargs):
        super(ADhocCallback, self).__init__(*args, **kwargs)
        self.result_row={'ok':{},'failed':{},'unreachable':{}}

    def v2_runner_on_ok(self, result,  *args, **kwargs):
        self.result_row['ok'][result._host.get_name()] = result._result
        logging.info('===v2_runner_on_ok===host=%s===result=%s' % (result._host.get_name(), result._result))


    def v2_runner_on_unreachable(self, result,*args,**kwargs):
        self.result_row['unreachable'][result._host.get_name()]=result._result

    def v2_runner_on_failed(self, result,  *args, **kwargs):
        self.result_row['failed'][result._host.get_name()]=result._result


class PlayBookCallback(CallbackBase):
    # CALLBACK_VERSION = 2.0
    def __init__(self, *args, **kwargs):
        super(PlayBookCallback, self).__init__(*args, **kwargs)
        self.result_row={'ok':{},'failed':{},'unreachable':{},'skipped':{},'status':{}}

    def v2_runner_on_ok(self, result,  *args, **kwargs):
        # print(result._host.get_name())
        # print("run on ok %s"%result._result)
        self.result_row['ok'][result._host.get_name()] = result._result

    def v2_runner_on_unreachable(self, result,*args,**kwargs):
        self.result_row['unreachable'][result._host.get_name()]=result._result

    def v2_runner_on_failed(self, result,  *args, **kwargs):
        self.result_row['failed'][result._host.get_name()]=result._result

    def v2_runner_on_skipped(self, result):
        self.result_row['skipped'][result._host.get_name()]=result._result

    def v2_playbook_on_stats(self, stats):
        # print(stats)
        hosts = sorted(stats.processed.keys())
        for h in hosts:
            t = stats.summarize(h)
            self.result_row['status'][h] = {
                                       "ok":t['ok'],
                                       "changed" : t['changed'],
                                       "unreachable":t['unreachable'],
                                       "skipped":t['skipped'],
                                       "failed":t['failures']
                                   }




class Runner():
    def __init__(self,resource=None):
        self.resource = resource
        self.inventory = None
        self.variable_manager = None
        self.loader = None
        self.options = None
        self.passwords = None
        self.callback = None
        self.__initializeData()
        self.results_raw = None

    def __initializeData(self):
        Options = namedtuple('Options', ['connection','module_path', 'forks', 'timeout',  'remote_user',
                'ask_pass', 'private_key_file', 'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args',
                'scp_extra_args', 'become', 'become_method', 'become_user', 'ask_value_pass', 'verbosity',
                'check', 'listhosts', 'listtasks', 'listtags', 'syntax','diff'])
        self.options = Options(connection='smart', module_path=None, forks=100, timeout=10,
                remote_user='root', ask_pass=False, private_key_file=None, ssh_common_args=None, ssh_extra_args=None,
                sftp_extra_args=None, scp_extra_args=None, become=None, become_method=None,
                become_user='root', ask_value_pass=False, verbosity=None, check=False, listhosts=False,
                listtasks=False, listtags=False, syntax=False, diff=True)
        self.passwords = dict(sshpass=None, becomepass=None)
        self.loader = DataLoader()

        # case1: no resource , use /etc/ansible/hosts
        if self.resource:
            myinventory = MyInventory(self.resource)
            self.inventory=myinventory.inventory
            self.variable_manager=myinventory.variable_manager

    def run_model(self, host_list, module_name, module_args):
        """
        ansible group1 -m shell -a 'ls /tmp'
        """
        self.callback = ADhocCallback()
        play_source = dict(
                name="Ansible Play",
                hosts=host_list,
                gather_facts='no',
                tasks=[dict(action=dict(module=module_name, args=module_args))]
        )
        play = Play().load(play_source, variable_manager=self.variable_manager, loader=self.loader)
        tqm = None
        try:
            tqm = TaskQueueManager(
                    inventory=self.inventory,
                    variable_manager=self.variable_manager,
                    loader=self.loader,
                    options=self.options,
                    passwords=self.passwords,
                    stdout_callback = "minimal",
            )
            tqm._stdout_callback = self.callback
            constants.HOST_KEY_CHECKING = False #关闭第一次使用ansible连接客户端是输入命令
            tqm.run(play)
            self.results_raw=self.callback.result_row
        except Exception as err:
            print(err)
        finally:
            if tqm is not None:
                tqm.cleanup()

    def run_playbook(self,playbookpath,extra_vars=None,localhostlist=None):
        # TODO log now is mixing in hostsresult . => play n/group /task n /

        # case1: no resource , use /etc/ansible/hosts
        if localhostlist:
            self.inventory=InventoryManager(loader=self.loader,sources=localhostlist)
            self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)

        self.callback=PlayBookCallback()
        try:
            # if self.redisKey:self.callback = PlayBookResultsCollectorToSave(self.redisKey,self.logId)
            if extra_vars:self.variable_manager.extra_vars = extra_vars
            executor = PlaybookExecutor(
                playbooks=[playbookpath],
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options,
                passwords=self.passwords,
            )
            executor._tqm._stdout_callback = self.callback
            constants.HOST_KEY_CHECKING = False #关闭第一次使用ansible连接客户端是输入命令
            executor.run()
            self.results_raw=self.callback.result_row
        except Exception as err:
            return False


def _example1():
    # test inventory
    resource={'group1':{'hosts':[{'hostid':'123','hostname':'h1','hostip':'192.168.188.200','username':'root',
                                  'password':'admin','port':'22','sshkey':'','k1':'v1'},
                                 {'hostid': '223', 'hostname': 'h2', 'hostip': '192.168.188.201', 'username': 'root',
                                  'password': '1qaz@WSX', 'port': '22', 'sshkey': '',},
                                 ],
                        'groupvars':{"g1key":"g1value"}},
              }
    # test inventory
    iobj=MyInventory(resource)
    iobj.testcase()


def _example2():
    # server playbook +  server inventory
    runner = Runner()
    runner.run_playbook(playbookpath='/etc/ansible/myplay.yaml', localhostlist=['/etc/ansible/hosts'])
    result = runner.results_raw
    print(json.dumps(result, indent=4))


def _example3():
    # server playbook  + dynamic inventory
    resource={'group1':{'hosts':[{'hostid':'123','hostname':'h1','hostip':'192.168.188.200','username':'root',
                                  'password':'admin','port':'22','sshkey':'','k1':'v1'},
                                 {'hostid': '223', 'hostname': 'h2', 'hostip': '192.168.188.201', 'username': 'root',
                                  'password': '1qaz@WSX', 'port': '22', 'sshkey': '',},
                                 ],
                        'groupvars':{"g1key":"g1value"}},
              }
    runner = Runner(resource)
    runner.run_playbook(playbookpath='/etc/ansible/myplay.yaml')



def _example4():
    #  use adhoc  + dynamic inventory
    # resource={'group1':{'hosts':[{'hostid':'123','hostname':'h1','hostip':'192.168.188.200','username':'root',
    #                               'password':'admin','port':'22','sshkey':'','k1':'v1'},
    #                              {'hostid': '223', 'hostname': 'h2', 'hostip': '192.168.188.201', 'username': 'root',
    #                               'password': '1qaz@WSX', 'port': '22', 'sshkey': '',},
    #                              ],
    #                     'groupvars':{"g1key":"g1value"}},
    #           }
    resource={'group1':{'hosts':[{'hostid':'123','hostname':'h1','hostip':'192.168.1.81','username':'root',
                                  'password':'root','port':'22','sshkey':'','k1':'v1'}
                                 ],
                        'groupvars':{"g1key":"g1value"}},
              }
    runner = Runner(resource)
    runner.run_model(host_list=['h2'], module_name='shell', module_args='ls /tmp')
    result = runner.results_raw
    print(result)


if __name__ == '__main__':


    # _example1()
    # _example2()
    # _example3()
    _example4()
#!/usr/bin/env python
# coding=utf-8
import json
import logging
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.plugins.callback import CallbackBase
from collections import namedtuple
from ansible import constants as C


class ResultsCollector(CallbackBase):

    def __init__(self,*args, **kwargs):
        super(ResultsCollector, self).__init__(*args, **kwargs)

    def _get_return_data(self, result):
        try:
            if result.get('msg',None):
                return_data= result.get('msg')
            elif result.get('stderr',None):
                return_data= result.get('stderr')
            else:
                return_data = result
        except:
            pass
        return return_data.encode('utf-8')

    def v2_runner_on_ok(self, result):
      host = result._host.get_name()
      self.runner_on_ok(host, result._result)
      logging.warning('===v2_runner_on_ok====host=%s===result=%s'%(host,result._result))

    def v2_runner_on_failed(self, result, ignore_errors=False):
      host = result._host.get_name()
      self.runner_on_failed(host, result._result, ignore_errors)
      return_data = self._get_return_data(result._result)
      logging.warning('===v2_runner_on_failed====host=%s===result=%s'%(host,return_data))

    def v2_runner_on_unreachable(self, result):
      host = result._host.get_name()
      self.runner_on_unreachable(host, result._result)
      return_data = self._get_return_data(result._result)
      logging.warning('===v2_runner_on_unreachable====host=%s===result=%s'%(host,return_data))

    def v2_runner_on_skipped(self, result):
        if C.DISPLAY_SKIPPED_HOSTS:
         host = result._host.get_name()
         self.runner_on_skipped(host, self._get_item(getattr(result._result,'results',{})))
         logging.warning("this task does not execute,please check parameter or condition.")

    def v2_playbook_on_stats(self, stats):
      logging.warning('===========palybook executes completed========')

loader = DataLoader()
variable_manager = VariableManager()
inventory = Inventory(loader = loader, variable_manager = variable_manager, host_list = ['127.0.0.1', '192.168.1.81'])
variable_manager.set_inventory(inventory)
variable_manager.extra_vars={"ansible_ssh_user":"root"} #额外参数，包括playbook参数 key:value

Options = namedtuple('Options',
                [ 'connection',
                 'remote_user',
                 'ask_sudo_pass',
                 'verbosity',
                 'ack_pass',
                 'module_path',
                 'forks',
                 'become',
                 'become_method',
                 'become_user',
                 'check',
                 'listhosts',
                 'listtasks',
                 'listtags',
                 'syntax',
                 'sudo_user',
                 'sudo'])

options = Options(
            connection='smart',
            remote_user='root',
            ack_pass=None,
            sudo_user='root',
            forks=200,
            sudo='yes',
            ask_sudo_pass=False,
            verbosity=5,
            module_path=None,
            become=True,
            become_method='su',
            become_user='root',
            check=None,
            listhosts=None,
            listtasks=None,
            listtags=None,
            syntax=None)

playbook = PlaybookExecutor(playbooks=['/tmp/playbook.yaml'],
                  inventory=inventory,
                  variable_manager=variable_manager,
                  loader=loader,
                  options=options,
                  passwords=None)
playbook._tqm._stdout_callback = ResultsCollector()
res = playbook.run()

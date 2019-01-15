#!/usr/bin/python
#--*--coding:utf-8--*--

import json
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.plugins.callback import CallbackBase


class Ansible_api:
    def __init__(self, hosts):
        self.loader = DataLoader()
        self.variable_manager = VariableManager()
        self.inventory = Inventory(loader=self.loader, variable_manager=self.variable_manager, host_list=hosts)
        self.variable_manager.set_inventory(self.inventory)
        Options = namedtuple("Options",
                             ['connection', 'forks', 'check', 'module_path', 'passwords', 'become', 'become_method',
                              'become_user', 'listhosts', 'listtasks', 'listtags', 'syntax'])
        self.options = Options(connection="smart", forks=5, check=False, module_path=None, passwords=None, become=None,
                               become_method=None, become_user=None, listhosts=None, listtasks=None, listtags=None,
                               syntax=None)

    def run_adhoc(self, module, args=""):
        play_source = {
            "name": "ansible api run_adhoc",
            "hosts": "all",
            "gather_facts": "no",
            "tasks": [
                {"action": {"module": module, "args": args}}
            ]
        }

        play = Play().load(play_source, variable_manager=self.variable_manager, loader=self.loader)
        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options,
                passwords=None,
                stdout_callback="minimal",
            )

            result = tqm.run(play)
            print
            result
        finally:
            if tqm is not None:
                tqm.cleanup()

    def run_playbook(self, yaml_file_list):
        # 这里extra_vars作用是为playbook yml文件传变量
        # self.variable_manager.extra_vars = {"host": host}
        pb = PlaybookExecutor(
            playbooks=yaml_file_list,
            inventory=self.inventory,
            variable_manager=self.variable_manager,
            loader=self.loader,
            passwords=None,
            options=self.options
        )
        result = pb.run()
        print
        result


if __name__ == "__main__":
    ansible_api = Ansible_api(["192.168.1.81"])
    ansible_api.run_adhoc("ping")
    ansible_api.run_adhoc("shell", "cat /etc/redhat-release")
    # ansible_api.run_playbook(["/etc/ansible/roles/jdk.yml"])




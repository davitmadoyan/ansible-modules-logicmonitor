ansible-modules-logicmonitor
=========
Ansible modules for interacting with Logicmonitor API to create, update or remove Logicmonitor devicegroups and devices.

Requirements
------------
An existing LogicMonitor account. These modules should always be performed on `localhost` (one can also use `delegate_to: localhost`). There are no benefits to running these tasks on the remote host since this module mostly preforms API calls to Logicmonitor's API server.

Usage
------------
Install the modules in `./roles` directory at the playbook level using `ansible-galaxy install` command and you will be able to use them in your playbook.
#### Example
```yaml
---
- src: 'git+https://github.ol.epicgames.net/IT/ansible-modules-logicmonitor.git'
  name: 'ansible-modules-logicmonitor'
  version: 'v1.1.0'
```
```
ansible-galaxy install --roles-path ./roles -r requirements.yml
```

Documentation
------------
Generate documentation for each module using `ansible-doc` command. For more details check [this](https://docs.ansible.com/ansible/latest/cli/ansible-doc.html)
#### Example
```
ansible-doc logicmonitor_device --module-path=/path/to/the/module/logicmonitor_device.py
```

Author Information
------------------

- Davit Madoyan <mad.davit.89@gmail.com>

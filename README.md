ansible-modules-logicmonitor
=========
Ansible modules for interacting with Logicmonitor API to create/update/remove Logicmonitor devicegroups and devices.

Requirements
------------
An existing LogicMonitor account. These modules should always be performed on localhost (one can also use "delegate_to: localhost"). There are no benefits to running these tasks on the remote host since this module mostly preforms API calls to Logicmonitor's API server.

Usage
------------
Install the modules in ./library directory at the playbook level using `ansible-galaxy install` command. Details can be found [here](https://docs.ansible.com/ansible/latest/dev_guide/developing_locally.html#adding-a-module-locally)
#### Example
```yaml
---
- src: 'git+https://github.ol.epicgames.net/IT/ansible-modules-logicmonitor.git'
  name: 'ansible-modules-logicmonitor'
  version: 'v1.1.0'
```
```
ansible-galaxy install --roles-path ./library -r requirements.yml
```


Module logicmonitor_device
------------
Module is used to create, update and remove Logicmonitor devices.
#### Module has the following options
```yaml
options:
  state:
    description:
      - The state (present/absent) of Logicmonitor object (device) you wish to manage
      - present: Creates the device if it doesn't exists or updates the device's params if there is a change.
      - absent: Removes the device from your Logicmonitor account
      - >
        NOTE This module should always be performed on localhost (one can also use "delegate_to: localhost"). There are no benefits to running these tasks on the
        remote host since this module mostly preforms API calls to Logicmonitor's API server.
    required: true
    default: null
    choices: ['present', 'absent']
  company:
    description:
      - The LogicMonitor account company name. If you would log in to your account at "superheroes.logicmonitor.com" you would use "superheroes"
    required: true
    default: null
  access_id:
    description:
      - Access ID of a Logicmonitor UI user. The module will authenticate and perform actions on behalf of this user.
    required: true
    default: None
  access_key:
    description:
        - The access key of the specified LogicMonitor Access ID.
    required: true
    default: None
  name:
    description:
      - The name of a device to manage in your Logicmonitor account.
    required: true
    default: None
  display_name:
    description:
      - The display name of a device in your Logicmonitor account.
      - Optional for managing hosts (target=host).
    required: true
    default: None
  description:
    description:
      - The long text description of the device in your Logicmonitor account.
    required: false
    default: ""
  collector_group_name:
    description:
      - Name of the autobalaned-collector group in your LogicMonitor account.
      - This is required for the creation of a LogicMonitor device.
    required: true
    default: None
  host_group_name:
    description:
        - Name of a host group that the host should be a member of.
    required: true
    default: None
  properties:
    description:
      - A list of dictionary of properties to set on the Logicmonitor device.
      - This parameter will add or update existing properties in your LogicMonitor account.
    required: false
    default: []
  alert_disable:
    description:
      - A boolean flag to turn alerting on or off for a device.
    required: false
    default: false
    choices: [true, false]
```
### Playbook examples
```yaml
#example of creating a Device
- hosts: localhost
  vars:
    company: mycompany
    access_id: my-access-id
    access_key: my-access-key
  tasks:
  - name: create a device
    logicmonitor_device:
      state: present
      company: '{{ company }}'
      access_id: '{{ access_id }}'
      access_key: '{{ access_key }}'
      name: device-1
      display_name: 'device-1'
      description: device-1
      host_group_name: test-1
      collector_group_name: test_Collector_group
      properties:
        - name: username
          value: password
#example of updating a Device
- hosts: localhost
  vars:
    company: mycompany
    access_id: my-access-id
    access_key: my-access-key
  tasks:
  - name: update description of the device
    logicmonitor_device:
      state: present
      company: '{{ company }}'
      access_id: '{{ access_id }}'
      access_key: '{{ access_key }}'
      name: device-1
      display_name: 'device-1'
      description: updated description
      host_group_name: test-1
      collector_group_name: test_Collector_group
      properties:
        - name: username
          value: password
#example of removing a Device
- hosts: localhost
  vars:
    company: mycompany
    access_id: my-access-id
    access_key: my-access-key
  tasks:
  - name: remove the device
    logicmonitor_device:
      state: absent
      company: '{{ company }}'
      access_id: '{{ access_id }}'
      access_key: '{{ access_key }}'
      name: device-1
      display_name: 'device-1'
```
Module logicmonitor_devicegroup
------------

Module is used to create, update and remove Logicmonitor devicegroups.
#### Module has the following options.
```yaml
options:
  state:
    description:
      - The state (present/absent) of Logicmonitor object (devicegroup) you wish to manage
      - present: Creates the device group if it doesn't exists or updates its params if there is a change.
      - absent: Removes the device group from your Logicmonitor account
      - >
        NOTE This module should always be performed on localhost (one can also use "delegate_to: localhost"). There are no benefits to running these tasks on the
        remote host since this module mostly preforms API calls to Logicmonitor's API server.
    required: true
    default: null
    choices: ['present', 'absent']
  company:
    description:
      - The LogicMonitor account company name. If you would log in to your account at "superheroes.logicmonitor.com" you would use "superheroes"
    required: true
    default: null
  access_id:
    description:
      - Access ID of a Logicmonitor UI user. The module will authenticate and perform actions on behalf of this user.
    required: true
    default: None
  access_key:
    description:
        - The access key of the specified LogicMonitor Access ID.
    required: true
    default: None
  name:
    description:
      - The name of a device group to manage in your Logicmonitor account.
    required: true
    default: None
  description:
    description:
      - The long text description of the device group in your Logicmonitor account.
    required: false
    default: ""
  collector_group_name:
    description:
      - Name of the autobalaned-collector group in your LogicMonitor account.
      - This is required for the creation of a LogicMonitor device group.
    required: true
    default: None
  parent_group_name:
    description:
        - Name of a device group that the created group should be a member of.
    required: false
    default: None
  properties:
    description:
      - A list of dictionary of properties to set on the Logicmonitor device group.
      - This parameter will add or update existing properties in your LogicMonitor account.
    required: false
    default: []
  alert_disable:
    description:
      - A boolean flag to turn alerting on or off for a device group.
    required: false
    default: false
    choices: [true, false]
```
#### Playbook examples
```yaml
#example of creating a Devicegroup
- hosts: localhost
  vars:
    company: mycompany
    access_id: my-access-id
    access_key: my-access-key
  tasks:
  - name: create a device group
    logicmonitor_devicegroup:
      state: present
      company: '{{ company }}'
      access_id: '{{ access_id }}'
      access_key: '{{ access_key }}'
      name: test-1
      description: test-1
      collector_group_name: test_Collector_group
      properties:
        - name: Customer1
          value: A
#example of updating a Devicegroup
- hosts: localhost
  vars:
    company: mycompany
    access_id: my-access-id
    access_key: my-access-key
  tasks:
  - name: update description of the device group
    logicmonitor_devicegroup:
      state: present
      company: '{{ company }}'
      access_id: '{{ access_id }}'
      access_key: '{{ access_key }}'
      name: test-1
      description: test-1.1 updated description
      collector_group_name: test_Collector_group
      properties:
        - name: Customer1
          value: A
#example of creating a Devicegroup inside another Devicegroup
- hosts: localhost
  vars:
    company: mycompany
    access_id: my-access-id
    access_key: my-access-key
  tasks:
  - name: create a Devicegroup inside another group
    logicmonitor_devicegroup:
      state: present
      company: '{{ company }}'
      access_id: '{{ access_id }}'
      access_key: '{{ access_key }}'
      parent_group_name: test-1
      name: test-2
      description: test-2
      collector_group_name: test_Collector_group
      properties:
        - name: Customer2
          value: B
#example of removing a Devicegroup (Note: if you remove a device group which has groups inside then that groups are removed as well)
- hosts: localhost
  vars:
    company: mycompany
    access_id: my-access-id
    access_key: my-access-key
  tasks:
  - name: remove a device
    logicmonitor_devicegroup:
      state: absent
      company: '{{ company }}'
      access_id: '{{ access_id }}'
      access_key: '{{ access_key }}'
      name: test-1
```

Author Information
------------------

- Davit Madoyan <davit.madoyan@epicgames.com>

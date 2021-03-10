#!/usr/bin/python

# LogicMonitor Ansible module for managing Devicegroups

DOCUMENTATION = '''
---
module: logicmonitor_devicegroup
short_description: Manage your Logicmonitor account through Ansible Playbooks
description:
  - This module manages device groups within your Logicmonitor account.
version_added: "2.9"
author: [Davit Madoyan <davit.madoyan@epicgames.com>]
notes:
  - You must have an existing Logicmonitor account for this module to function.
requirements: ["An existing Logicmonitor account"]
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
...
'''
Examples = '''
#example of creating a Devicegroup
---
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
---
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
---
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
---
#example of removing a Devicegroup (Note: if you remove a device group which has groups inside then that groups are removed as well)
---
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
---
'''

import json
import hashlib
import base64
import time
import hmac
import requests

from ansible.module_utils.basic import AnsibleModule


class Devicegroup():

    def __init__(self, params, module):
        """Initializor for the LogicMonitor Devicegroup class"""
        self.change = False
        self.params = params
        self.module = module
        self.module.debug("Instantiating Devicegroup object")

        self.check_mode = False
        self.company = params["company"]
        self.access_id = params["access_id"]
        self.access_key = params["access_key"]
        self.lm_url = "logicmonitor.com/santaba/rest"

        self.name = self.params["name"]
        self.properties = self.params["properties"]
        self.description = self.params["description"]
        self.parent_group_name = self.params["parent_group_name"]
        self.alert_disable = self.params["alert_disable"]
        self.collector_group_name = self.params["collector_group_name"]

        self.info = self.get_group(self.name)

    def rest_api(self, httpverb, resourcepath, query_params="", data=""):
        """Make a call to the LogicMonitor REST API
        and return the response"""
        self.module.debug("Running LogicMonitor.REST API")

        #Construct URL
        url = 'https://' + self.company + '.' + self.lm_url + resourcepath + query_params

        #Get current time in milliseconds
        epoch = str(int(time.time() * 1000))

        #Concatenate Request details
        if isinstance(data, dict):
            data = json.dumps(data)
        requestvars = httpverb + epoch + data + resourcepath

        #Construct signature
        hmac_hash = hmac.new(self.access_key.encode(), msg=requestvars.encode(),
                             digestmod=hashlib.sha256).hexdigest()
        signature = base64.b64encode(hmac_hash.encode())

        #Construct headers and make request
        auth = 'LMv1 ' + self.access_id + ':' + signature.decode() + ':' + epoch
        try:
            if "collector" in resourcepath:
                headers = {'Content-Type':'application/json', 'x-version':'3', 'Authorization':auth}
                response = requests.get(url, data=data, headers=headers)
            elif httpverb == "GET":
                headers = {'Content-Type':'application/json', 'Authorization':auth}
                response = requests.get(url, data=data, headers=headers)
            elif httpverb == "POST":
                headers = {'Content-Type':'application/json', 'x-version':'3', 'Authorization':auth}
                response = requests.post(url, data=data, headers=headers)
            elif httpverb == "DELETE":
                headers = {'Content-Type':'application/json', 'x-version':'3', 'Authorization':auth}
                response = requests.delete(url, data=data, headers=headers)
            elif httpverb == "PUT":
                headers = {'Content-Type':'application/json', 'x-version':'3', 'Authorization':auth}
                response = requests.put(url, data=data, headers=headers)
        except Exception as error:
            self.change = False
            self.module.fail_json(
                msg="REST API call to {} endpoint has failed. ".format(resourcepath) +
                "Error_msg: {}".format(error), changed=self.change, failed=True)

        return response.json()

    def get_group(self, name):
        """Returns a JSON group object for the group matching the
        specified name"""
        self.module.debug("Running LogicMonitor.get_group...")

        self.module.debug("Making REST API call to /device/groups endpoint")
        resp = self.rest_api("GET", "/device/groups", "?filter=name:{}".format(name))

        if resp["status"] == 200:
            self.module.debug("REST API called succeeded")
            if  len(resp["data"]["items"]) > 0:
                return resp["data"]["items"][0]
            self.module.debug("No device match found")
            return None
        self.module.debug("REST API call failed")
        self.change = False
        self.module.fail_json(
            msg="Error: unable to get the group " +
            "Error_msg: {}".format(resp), changed=self.change, failed=True)

    def create_or_update(self):
        """Idempotent function to ensure the host group settings
        in the LogicMonitor account match the current object."""
        self.module.debug("Running Devicegroup.create_or_update")

        if self.info is not None:
            changed, take_manual = self.is_changed()
            if changed:
                self.module.debug("Group exists. Updating its parameters")
                body = self._build_host_group_dict()
                if take_manual:
                  body["disableAlerting"] = 'true'
                resp = self.rest_api("PUT", "/device/groups/{}".format(str(self.info["id"])), "", body)
                return resp
            else:
                self.change = False
                self.module.exit_json(changed=self.change, success=True)
        self.module.debug("Group doesn't exist. Creating.")
        self.module.debug("System changed")
        if self.check_mode:
            self.change = False
            self.module.exit_json(changed=self.change, success=True)
        result = self.add()
        return result

    def is_changed(self):
        """Return true if the Devicegroup doesn't match
        the LogicMonitor account"""
        self.module.debug("Running Devicegroup.is_changed...")

        group = self.info
        properties = self._build_host_group_dict()
        changed = False

        take_manual = False
        # check if the disableAlerting is set to 'true' manually from the UI and if so don't override it
        if (str(group["disableAlerting"]).lower() == 'true' and  properties["disableAlerting"].lower() == 'false'):
            take_manual = True

        if properties is not None and group is not None:
            self.module.debug("Comparing simple group properties")
            if (str(group["disableAlerting"]).lower() != properties["disableAlerting"].lower() or
                    group["description"] != properties["description"] or
                    group["parentId"] != properties["parentId"] or
                    group["defaultCollectorGroupId"] != properties["defaultCollectorGroupId"]):
                changed = True
                return changed, take_manual
            changed = any(i not in properties["customProperties"] for i in group["customProperties"])
            if changed:
                return changed, take_manual
            changed = any(i not in group["customProperties"] for i in properties["customProperties"])
            return changed, take_manual
        else:
            self.module.debug("No property information received")
            return changed, take_manual

    def add(self):
        """Idempotent function to ensure that the host
        group exists in your LogicMonitor account"""
        self.module.debug("Running Devicegroup.add")

        self.module.debug("Group doesn't exist. Creating.")
        self.module.debug("System changed")
        if self.check_mode:
            self.change = False
            self.module.exit_json(changed=self.change, success=True)
        body = self._build_host_group_dict()
        self.module.debug("Making REST API call to '/device/groups'")
        resp = self.rest_api("POST", "/device/groups", "", body)
        if "name" in resp.keys() and resp["name"] == self.name:
            self.module.debug("REST API call succeeded")
            self.module.debug("Group created")
            return resp
        # errorCode - 1400,1409: Device group with the provided name and params already exists.
        if resp['errorCode'] == 1409 or resp['errorCode'] == 1400:
            self.module.exit_json(msg=resp, changed=False, success=True)
        self.module.debug("REST API call failed")
        self.change = False
        self.module.fail_json(
            msg="Error: unable to create the new device group {}. ".format(self.name) +
            "Error_msg: {}".format(resp), changed=self.change, failed=True)

    def get_collector_groups(self):
        """Returns a JSON object containing a list of
        LogicMonitor collector groups"""
        self.module.debug("Running LogicMonitor get_collector_groups...")

        self.module.debug("Making REST API call to '/setting/collector/groups'")
        resp = self.rest_api("GET", "/setting/collector/groups")
        if resp["total"] >= 0:
            self.module.debug("REST API call succeeded")
            return resp
        self.module.debug("REST API call failed")
        self.change = False
        self.module.fail_json(
            msg="Error: unable to get the collector groups " +
            "Error_msg: {}".format(resp), changed=self.change, failed=True)

    def get_collector_group_by_name(self):
        """Returns a JSON collector_group object for the collector group
        matching the specified (name)"""
        self.module.debug("Running LogicMonitor.get_collector_group_by_name...")

        collector_groups = self.get_collector_groups()
        self.module.debug(
            "Looking for collector group with " +
            "name {}".format(self.collector_group_name))
        for collector_group in collector_groups["items"]:
            if collector_group["name"] == self.collector_group_name:
                self.module.debug("Collector group match found")
                return collector_group
        self.module.debug("No collector group match found")
        self.change = False
        self.module.fail_json(
            msg="No collector group match found " +
            "for {}".format(self.collector_group_name), changed=self.change, failed=True)

    def _build_host_group_dict(self):
        """Returns a dict with host group params"""
        if self.parent_group_name is None:
            parent_id = 1
        else:
            parentgroup = self.get_group(self.parent_group_name)
            parent_id = parentgroup["id"]
        collector_group_data = self.get_collector_group_by_name()
        collector_group_id = collector_group_data["id"]
        body_dict = {"name": self.name,
                     "parentId": parent_id,
                     "disableAlerting": self.alert_disable,
                     "description": self.description,
                     "customProperties": self.properties,
                     "defaultCollectorGroupId": collector_group_id,
                     "defaultCollectorId": 0,
                     "defaultAutoBalancedCollectorGroupId": collector_group_id}
        return body_dict

    def remove(self):
        """Idempotent function to ensure the host group
        does not exist in your LogicMonitor account"""
        self.module.debug("Running Devicegroup.remove...")

        if self.info is not None:
            self.module.debug("Group exists")
            self.module.debug("System changed")
            self.change = True
            if self.check_mode:
                self.change = False
                self.module.exit_json(changed=self.change, success=True)
            self.module.debug("Making REST API call to 'deleteDevicegroup'")
            resp = self.rest_api("DELETE", "/device/groups/{}".format(str(self.info["id"])))
            self.module.exit_json(changed=self.change, msg=resp)
            self.module.debug("REST API call succeeded")
            return resp
        else:
            self.module.debug("Group doesn't exist")
            self.change = False
            self.module.exit_json(changed=self.change, success=True)

def main():
    """Define available arguments/parameters a user
    can pass to the module"""
    state = [
        "present",
        "absent"]

    module_args = dict(
        state=dict(required=True, default=None, choices=state),
        company=dict(required=True, default=None),
        access_id=dict(required=True, default=None),
        access_key=dict(required=True, default=None, no_log=True),

        name=dict(required=True, default=None),
        description=dict(required=False, default=""),
        collector_group_name=dict(required=True, default=None),
        parent_group_name=dict(required=False, default=None),
        properties=dict(required=False, default=[], type="list"),
        alert_disable=dict(required=False, default="false")
    )

    result = dict(
        changed=False,
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    target = Devicegroup(module.params, module)

    if module.params["state"].lower() == "present":
        output = target.create_or_update()
    elif module.params["state"].lower() == "absent":
        output = target.remove()

    result["changed"] = True
    result["message"] = output
    module.exit_json(**result)


if __name__ == "__main__":
    main()

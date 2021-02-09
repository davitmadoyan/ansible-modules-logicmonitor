#!/usr/bin/python

# LogicMonitor Ansible module for managing Devices

DOCUMENTATION = '''
---
module: logicmonitor_device
short_description: Manage your Logicmonitor account through Ansible Playbooks
description:
  - This module manages devices within your LogicMonitor account.
version_added: "2.9"
author: [Davit Madoyan <davit.madoyan@epicgames.com>]
notes:
  - You must have an existing Logicmonitor account for this module to function.
requirements: ["An existing LogicMonitor account"]
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
  netflow_collector_name:
    description:
      - Name of a collector to send the NetFlow data to.
    required: false
    default: None
...
'''
Examples = '''
#example of creating a Device
---
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
      netflow_collector_name: test-collector.example.com
      properties:
        - name: username
          value: password
#example of updating a Device
---
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
---
#example of removing a Device
---
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
---
'''

import json
import hashlib
import base64
import time
import hmac
import requests

from ansible.module_utils.basic import AnsibleModule


class Device():

    def __init__(self, params, module):
        """Initializor for the LogicMonitor Device class"""
        self.change = False
        self.params = params
        self.module = module
        self.module.debug("Instantiating Device object")

        self.check_mode = False
        self.company = params["company"]
        self.access_id = params["access_id"]
        self.access_key = params["access_key"]
        self.lm_url = "logicmonitor.com/santaba/rest"

        self.name = self.params["name"]
        self.display_name = self.params["display_name"]
        self.properties = self.params["properties"]
        self.description = self.params["description"]
        self.host_group_name = self.params["host_group_name"]
        self.alert_disable = self.params["alert_disable"]
        self.collector_group_name = self.params["collector_group_name"]
        self.netflow_collector_name = self.params["netflow_collector_name"]

        self.info = self.get_device(self.name)

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
            if "collector/groups" in resourcepath:
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

    def get_device(self, name):
        """Returns a JSON device object for the device matching the
        specified name"""
        self.module.debug("Running LogicMonitor.get_device...")

        self.module.debug("Making REST API call to /device/devices endpoint")
        resp = self.rest_api("GET", "/device/devices", "?filter=name:{}".format(name))

        if resp["status"] == 200:
            self.module.debug("REST API called succeeded")
            if  len(resp["data"]["items"]) > 0:
                return resp["data"]["items"][0]
            self.module.debug("No device match found")
            return None
        self.module.debug("REST API call failed")
        self.change = False
        self.module.fail_json(
            msg="Error: unable to get the device " +
            "Error_msg: {}".format(resp), changed=self.change, failed=True)

    def get_group(self, name):
        """Returns a JSON group object for the group matching the
        specified name"""
        self.module.debug("Running LogicMonitor.get_group...")

        self.module.debug("Making REST API call to /device/groups endpoint")
        resp = self.rest_api("GET", "/device/groups", "?filter=name:{}&fields=id,name".format(name))

        if resp["status"] == 200 and resp["data"] != None:
            self.module.debug("Group match found")
            return resp["data"]["items"][0]
        self.module.debug("REST API call failed")
        self.change = False
        self.module.fail_json(
            msg="Error: unable to get the group " +
            "Error_msg: {}".format(resp), changed=self.change, failed=True)

    def create_or_update(self):
        """Idempotent function to ensure the host settings
        in the LogicMonitor account match the current object."""
        self.module.debug("Running Device.create_or_update")

        if self.info is not None:
            if self.is_changed():
                self.module.debug("Device exists. Updating its parameters")
                body = self._build_host_dict()
                resp = self.rest_api("PUT", "/device/devices/{}".format(str(self.info["id"])), "", body)
                return resp
            else:
                self.change = False
                self.module.exit_json(changed=self.change, success=True)
        self.module.debug("Device doesn't exist. Creating.")
        self.module.debug("System changed")
        if self.check_mode:
            self.change = False
            self.module.exit_json(changed=self.change, success=True)
        result = self.add()
        return result

    def is_changed(self):
        """Return true if the Device doesn't match
        the LogicMonitor account"""
        self.module.debug("Running Device.is_changed...")

        device = self.info
        properties = self._build_host_dict()
        changed = False
        if properties is not None and device is not None:
            self.module.debug("Comparing simple device properties")
            if (str(device["disableAlerting"]).lower() != properties["disableAlerting"].lower() or
                    device["description"] != properties["description"] or
                    device["displayName"] != properties["displayName"] or
                    str(device["hostGroupIds"]) != str(properties["hostGroupIds"]) or
                    device["preferredCollectorGroupId"] != properties["autoBalancedCollectorGroupId"]):
                changed = True
                return changed
            changed = any(i not in properties["customProperties"] for i in device["customProperties"])
            if changed:
                return changed
            changed = any(i not in device["customProperties"] for i in properties["customProperties"])
            return changed
        else:
            self.module.debug("No property information received")
            return False

    def add(self):
        """Idempotent function to ensure that the host
        exists in your LogicMonitor account"""
        self.module.debug("Running Device.add")

        self.module.debug("Device doesn't exist. Creating.")
        self.module.debug("System changed")
        if self.check_mode:
            self.change = False
            self.module.exit_json(changed=self.change, success=True)
        body = self._build_host_dict()
        self.module.debug("Making REST API call to '/device/devices'")
        resp = self.rest_api("POST", "/device/devices", "", body)
        if "name" in resp.keys() and resp["name"] == self.name:
            self.module.debug("REST API call succeeded")
            self.module.debug("device created")
            return resp
        self.module.debug("REST API call failed")
        self.change = False
        self.module.fail_json(
            msg="Error: unable to create the new device {}. ".format(self.name) +
            "Error: {}".format(resp), changed=self.change, failed=True)

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

    def get_collector_by_name(self, name):
        """Returns a JSON collector object for the collector matching the
        specified name"""
        self.module.debug("Running LogicMonitor.get_collector_by_name...")

        self.module.debug("Making REST API call to /setting/collectors endpoint")
        resp = self.rest_api("GET", "/setting/collectors", "?filter=description:{}&fields=id,description".format(name))

        if resp["status"] == 200 and resp["data"] != None:
            self.module.debug("Group match found")
            return resp["data"]["items"][0]
        self.module.debug("REST API call failed")
        self.change = False
        self.module.fail_json(
            msg="Error: unable to get the collector " +
            "Error_msg: {}".format(resp), changed=self.change, failed=True)

    def _build_host_dict(self):
        """Returns a dict with device params"""
        if self.host_group_name is None:
            host_group_id = 1
        else:
            host_group = self.get_group(self.host_group_name)
            host_group_id = host_group["id"]
        if self.netflow_collector_name is not None:
            enble_netflow = "true"
            netflow_collector_data = self.get_collector_by_name(self.netflow_collector_name)
            netflow_collector_id = netflow_collector_data["id"]
        else:
            enble_netflow = "false"
            netflow_collector_id = 0

        collector_group_data = self.get_collector_group_by_name()
        collector_group_id = collector_group_data["id"]
        body_dict = {"name": self.name,
                     "displayName": self.display_name,
                     "hostGroupIds": host_group_id,
                     "disableAlerting": self.alert_disable,
                     "description": self.description,
                     "customProperties": self.properties,
                     "preferredCollectorId": 0,
                     "autoBalancedCollectorGroupId": collector_group_id,
                     "enableNetflow": enble_netflow,
                     "netflowCollectorId": netflow_collector_id}
        return body_dict

    def remove(self):
        """Idempotent function to ensure the device
        does not exist in your LogicMonitor account"""
        self.module.debug("Running Device.remove...")

        if self.info is not None:
            self.module.debug("Device exists")
            self.module.debug("System changed")
            self.change = True
            if self.check_mode:
                self.change = False
                self.module.exit_json(changed=self.change, success=True)
            self.module.debug("Making REST API call to 'deleteDevice'")
            resp = self.rest_api("DELETE", "/device/devices/{}".format(str(self.info["id"])))
            self.module.exit_json(changed=self.change, msg=resp)
            self.module.debug("REST API call succeeded")
            return resp
        else:
            self.module.debug("Device doesn't exist")
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
        display_name=dict(required=True, default=None),
        description=dict(required=False, default=""),
        collector_group_name=dict(required=True, default=None),
        host_group_name=dict(required=True, default=None),
        properties=dict(required=False, default=[], type="list"),
        alert_disable=dict(required=False, default="false"),
        netflow_collector_name=dict(required=False, default=None)
    )

    result = dict(
        changed=False,
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    target = Device(module.params, module)

    if module.params["state"].lower() == "present":
        output = target.create_or_update()
    elif module.params["state"].lower() == "absent":
        output = target.remove()

    result["changed"] = True
    result["message"] = output
    module.exit_json(**result)


if __name__ == "__main__":
    main()

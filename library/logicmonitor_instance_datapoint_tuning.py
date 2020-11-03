#!/usr/bin/python

# LogicMonitor Ansible module for managing instance level and/or datapoint level alert/treshold tunning.

DOCUMENTATION = '''
---
module: logicmonitor_instance_datapoint_tuning.py
short_description: Manage your Logicmonitor account through Ansible Playbooks
description:
  - This module tunes instance/datapoint alering/threshold within your LogicMonitor account.
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
  display_name:
    description:
      - The display name of a device in your Logicmonitor account.
    required: true
    default: None
  datasource_displayname:
    description:
      - The display name of a datasource in your Logicmonitor account.
    required: true
    default: None
  instance_name:
    description:
      - The name of an instance of a datasource for a device in your Logicmonitor account.
    required: true
    default: None
  datapoint_name:
    description:
      - The name of a datapoint of an instance of a datasource for a device in your Logicmonitor account.
    required: false
    default: None
  alert_disable:
    description:
      - A boolean flag to turn alerting on or off for a device.
    required: false
    default: false
    choices: [true, false]
  threshold:
    description:
      - The desired threshold a datapoint of an instance of a datasource for a device in your Logicmonitor account.
    required: false
    default: None
...
'''
Examples = '''
#example of disabling alerting for Ethernet1/1 interface
---
- hosts: localhost
  vars:
    company: mycompany
    access_id: my-access-id
    access_key: my-access-key
  tasks:
  - name: disable alerting for Ethernet1/1 interface of device.example.com device
    logicmonitor_instance_datapoint_tuning:
      state: present
      company: '{{ company }}'
      access_id: '{{ access_id }}'
      access_key: '{{ access_key }}'
      device_displayname: 'device.example.com'
      datasource_displayname: 'Interfaces (64 bit)-'
      instance_name: 'Ethernet1/1'
      alert_disable: 'true'
---
#example of disabling alerting for status datapoint of Ethernet1/1 interface
---
- hosts: localhost
  vars:
    company: mycompany
    access_id: my-access-id
    access_key: my-access-key
  tasks:
  - name: disabl alerting for status datapoint of Ethernet1/1 interface of device.example.com device
    logicmonitor_instance_datapoint_tuning:
      state: absent
      company: '{{ company }}'
      access_id: '{{ access_id }}'
      access_key: '{{ access_key }}'
      device_displayname: 'device.example.com'
      datasource_displayname: 'Interfaces (64 bit)-'
      instance_name: 'Ethernet1/1'
      datapoint_name: 'Status'
      alert_disable: 'true'
#example of changing threshold for status datapoint of Ethernet1/1 interface
---
- hosts: localhost
  vars:
    company: mycompany
    access_id: my-access-id
    access_key: my-access-key
  tasks:
  - name: change threshold for status datapoint of Ethernet1/1 interface of device.example.com device
    logicmonitor_instance_datapoint_tuning:
      state: absent
      company: '{{ company }}'
      access_id: '{{ access_id }}'
      access_key: '{{ access_key }}'
      device_displayname: 'device.example.com'
      datasource_displayname: 'Interfaces (64 bit)-'
      instance_name: 'Ethernet1/1'
      datapoint_name: 'Status'
      threshold: '> 1'
---
'''


import json
import hashlib
import base64
import time
import hmac
import requests

from ansible.module_utils.basic import AnsibleModule


class Tuning():
    LM_URL = "logicmonitor.com/santaba/rest"

    def __init__(self, params, module):
        """Initializor for the LogicMonitor Tuning class"""
        self.change = False
        self.params = params
        self.module = module
        self.module.debug("Instantiating Tuning object")

        self.check_mode = False
        self.company = params["company"]
        self.access_id = params["access_id"]
        self.access_key = params["access_key"]

        self.device_displayname = self.params["device_displayname"]
        self.datasource_displayname = self.params["datasource_displayname"]
        self.instance_name = self.params["instance_name"]
        self.datapoint_name = self.params["datapoint_name"]
        self.threshold = self.params["threshold"]
        self.alert_disable = self.params["alert_disable"]

    def rest_api(self, httpverb, resourcepath, params):
        """Make a call to the LogicMonitor REST API
        and return the response"""
        self.module.debug("Running LogicMonitor.REST API")

        #Construct URL
        url = 'https://' + self.company + "." + self.LM_URL + resourcepath

        #Get current time in milliseconds
        epoch = str(int(time.time() * 1000))

        #Concatenate Request details
        params_string = ""
        if isinstance(params, dict):
            params_string = json.dumps(params)
        requestvars = httpverb + epoch + params_string + resourcepath

        #Construct signature
        hmac_hash = hmac.new(self.access_key.encode(), msg=requestvars.encode(),
                             digestmod=hashlib.sha256).hexdigest()
        signature = base64.b64encode(hmac_hash.encode())

        #Construct headers and make request
        auth = 'LMv1 ' + self.access_id + ':' + signature.decode() + ':' + epoch
        try:
            headers = {'Content-Type':'application/json', 'x-version':'3', 'Authorization':auth}
            if "collector" in resourcepath:
                response = requests.get(url, data=params_string, headers=headers)
            elif httpverb == "GET":
                headers = {'Content-Type':'application/json', 'Authorization':auth}
                response = requests.get(url, data=params_string, headers=headers)
            elif httpverb == "POST":
                response = requests.post(url, data=params_string, headers=headers)
            elif httpverb == "DELETE":
                response = requests.delete(url, data=params_string, headers=headers)
            elif httpverb == "PUT":
                response = requests.put(url, data=params_string, headers=headers)
        except Exception as error:
            self.change = False
            self.module.fail_json(
                msg="REST API call to {} endpoint has failed. ".format(resourcepath) +
                "Error_msg: {}".format(error), changed=self.change, failed=True)

        return response.json()

    def get_device(self):
        """Returns a JSON device object for the device matching the
        specified name"""
        self.module.debug("Running LogicMonitor.get_device...")

        self.module.debug("Making REST API call to /device/devices endpoint")
        resp = self.rest_api("GET", "/device/devices", "")
        return self.parse_response(resp, "displayName", self.device_displayname)

    def get_datasource(self, device_id):
        """Returns a JSON datasource object for the datasource matching the
        specified name"""
        self.module.debug("Running LogicMonitor.get_datasource...")

        self.module.debug("Making REST API call to /device/devices/device_id/devicedatasources endpoint")
        resp = self.rest_api("GET", "/device/devices/{}/devicedatasources".format(device_id), "")
        return self.parse_response(resp, "dataSourceDisplayName", self.datasource_displayname)

    def get_instance(self, device_id, datasource_id):
        """Returns a JSON instance object for the instance matching the
        specified name"""
        self.module.debug("Running LogicMonitor.get_instance...")

        self.module.debug("Making REST API call to /device/devices/device_id/devicedatasources/datasource_id/instances endpoint")
        resp = self.rest_api("GET", "/device/devices/{}/devicedatasources/{}/instances".format(device_id, datasource_id), "")
        return self.parse_response(resp, "displayName", self.instance_name)

    def get_datapoint(self, device_id, datasource_id, instance_id):
        """Returns a JSON datapoint object for the datapoint matching the
        specified name"""
        self.module.debug("Running LogicMonitor.get_datapoint...")

        self.module.debug("Making REST API call to /device/devices/device_id/devicedatasources/datasource_id/instances/instance_id/alertsettings endpoint")
        resp = self.rest_api("GET", "/device/devices/{}/devicedatasources/{}/instances/{}/alertsettings".format(device_id, datasource_id, instance_id), "")
        return self.parse_response(resp, "dataPointName", self.datapoint_name)

    def parse_response(self, resp, matching_key, matching_param):
        if resp["status"] == 200:
            self.module.debug("REST API called succeeded")
            items = resp["data"]
            self.module.debug("Looking for matching to" + matching_param)
            for item in items["items"]:
                if item[matching_key] == matching_param:
                    self.module.debug("Match found")
                    return item
            self.module.debug("No match found")
            self.module.fail_json(
                msg="Error: No match found with the provided name: {}".format(matching_param), changed=self.change, failed=True)
        self.module.debug("REST API call failed")
        self.change = False
        self.module.fail_json(
            msg="Error: API call didn't return any data " +
            "Error_msg: {}".format(resp), changed=self.change, failed=True)

    def alert_threshold_tuning(self):
        """Idempotent function to ensure the alert or threshold settings
        in the LogicMonitor account match the current object."""
        self.module.debug("Running Device.alert_threshold_tuning")

        self.device = self.get_device()
        self.datasource = self.get_datasource(str(self.device["id"]))
        self.instance = self.get_instance(str(self.device["id"]), str(self.datasource["id"]))

        data = {}
        if self.datapoint_name is not None:
          self.datapoint = self.get_datapoint(str(self.device["id"]), str(self.datasource["id"]), str(self.instance["id"]))
          if self.threshold is not None:
            if self.check_mode:
                self.change = False
                self.module.exit_json(changed=self.change, success=True)
            data["alertExpr"] = self.threshold
            resp = self.rest_api("PUT", "/device/devices/{}/devicedatasources/{}/instances/{}/alertsettings/{}".format(str(self.device["id"]), str(self.datasource["id"]), str(self.instance["id"]), str(self.datapoint["id"])), data)
            return resp
          else:
            if self.check_mode:
                self.change = False
                self.module.exit_json(changed=self.change, success=True)
            data["disableAlerting"] = self.alert_disable
            resp = self.rest_api("PUT", "/device/devices/{}/devicedatasources/{}/instances/{}/alertsettings/{}".format(str(self.device["id"]), str(self.datasource["id"]), str(self.instance["id"]), str(self.datapoint["id"])), data)
            return resp
        else:
          if self.check_mode:
              self.change = False
              self.module.exit_json(changed=self.change, success=True)
          data["disableAlerting"] = self.alert_disable
          data["displayName"] = self.instance["displayName"]
          data["wildValue"] = self.instance["wildValue"]
          resp = self.rest_api("PUT", "/device/devices/{}/devicedatasources/{}/instances/{}".format(str(self.device["id"]), str(self.datasource["id"]), str(self.instance["id"])), data)
          return resp

def main():
    """Define available arguments/parameters a user
    can pass to the module"""

    module_args = {
        "company": dict(required=True, default=None),
        "access_id": dict(required=True, default=None),
        "access_key": dict(required=True, default=None, no_log=True),

        "device_displayname": dict(required=True, default=None),
        "datasource_displayname": dict(required=True, default=None),
        "instance_name": dict(required=True, default=None),
        "datapoint_name": dict(required=False, default=None),
        "alert_disable": dict(required=False, default="false"),
        "threshold": dict(required=False, default=None)
    }

    result = {
        "changed": True,
        "message": ''
    }

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    target = Tuning(module.params, module)

    output = target.alert_threshold_tuning()

    result["message"] = output
    module.exit_json(**result)


if __name__ == "__main__":
    main()

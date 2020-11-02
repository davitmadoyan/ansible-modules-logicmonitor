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
        self.lm_url = "logicmonitor.com/santaba/rest"

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
        url = 'https://' + self.company + "." + self.lm_url + resourcepath

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
            if "collector" in resourcepath:
                headers = {'Content-Type':'application/json', 'x-version':'3', 'Authorization':auth}
                response = requests.get(url, data=params_string, headers=headers)
            elif httpverb == "GET":
                headers = {'Content-Type':'application/json', 'Authorization':auth}
                response = requests.get(url, data=params_string, headers=headers)
            elif httpverb == "POST":
                headers = {'Content-Type':'application/json', 'x-version':'3', 'Authorization':auth}
                response = requests.post(url, data=params_string, headers=headers)
            elif httpverb == "DELETE":
                headers = {'Content-Type':'application/json', 'x-version':'3', 'Authorization':auth}
                response = requests.delete(url, data=params_string, headers=headers)
            elif httpverb == "PUT":
                headers = {'Content-Type':'application/json', 'x-version':'3', 'Authorization':auth}
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
        if resp["status"] == 200:
            self.module.debug("REST API called succeeded")
            devices = resp["data"]
            self.module.debug("Looking for device matching " + self.device_displayname)
            for device in devices["items"]:
                if device["displayName"] == self.device_displayname:
                    self.module.debug("device match found")
                    return device
            self.module.debug("No device match found")
            self.module.fail_json(
                msg="Error: No device found with the provided name: {}".format(self.device_displayname), changed=self.change, failed=True)
        self.module.debug("REST API call failed")
        self.change = False
        self.module.fail_json(
            msg="Error: unable to get the devices " +
            "Error_msg: {}".format(resp), changed=self.change, failed=True)

    def get_datasource(self, device_id):
        """Returns a JSON datasource object for the datasource matching the
        specified name"""
        self.module.debug("Running LogicMonitor.get_datasource...")

        self.module.debug("Making REST API call to /device/devices/device_id/devicedatasources endpoint")
        resp = self.rest_api("GET", "/device/devices/{}/devicedatasources".format(device_id), "")
        if resp["status"] == 200:
            self.module.debug("REST API called succeeded")
            datasources = resp["data"]
            self.module.debug("Looking for datasource matching " + device_id)
            for datasource in datasources["items"]:
                if datasource["dataSourceDisplayName"] == self.datasource_displayname:
                    self.module.debug("Datasource match found")
                    return datasource
            self.module.debug("No datasource match found")
            self.module.fail_json(
                msg="Error: No datasource found with the provided name: {}".format(self.datasource_displayname), changed=self.change, failed=True)
        self.module.debug("REST API call failed")
        self.change = False
        self.module.fail_json(
            msg="Error: unable to get the datasources " +
            "Error_msg: {}".format(resp), changed=self.change, failed=True)

    def get_instance(self, device_id, datasource_id):
        """Returns a JSON instance object for the instance matching the
        specified name"""
        self.module.debug("Running LogicMonitor.get_instance...")

        self.module.debug("Making REST API call to /device/devices/device_id/devicedatasources/datasource_id/instances endpoint")
        resp = self.rest_api("GET", "/device/devices/{}/devicedatasources/{}/instances".format(device_id, datasource_id), "")
        if resp["status"] == 200:
            self.module.debug("REST API called succeeded")
            instances = resp["data"]
            self.module.debug("Looking for instance matching " + device_id)
            for instance in instances["items"]:
                if instance["displayName"] == self.instance_name:
                    self.module.debug("Instance match found")
                    return instance
            self.module.debug("No instance match found")
            self.module.fail_json(
                msg="Error: No instance with the provided name: {}".format(self.instance_name), changed=self.change, failed=True)
        self.module.debug("REST API call failed")
        self.change = False
        self.module.fail_json(
            msg="Error: unable to get the instances " +
            "Error_msg: {}".format(resp), changed=self.change, failed=True)

    def get_datapoint(self, device_id, datasource_id, instance_id):
        """Returns a JSON datapoint object for the datapoint matching the
        specified name"""
        self.module.debug("Running LogicMonitor.get_datapoint...")

        self.module.debug("Making REST API call to /device/devices/device_id/devicedatasources/datasource_id/instances/instance_id/alertsettings endpoint")
        resp = self.rest_api("GET", "/device/devices/{}/devicedatasources/{}/instances/{}/alertsettings".format(device_id, datasource_id, instance_id), "")
        if resp["status"] == 200:
            self.module.debug("REST API called succeeded")
            datapoints = resp["data"]
            self.module.debug("Looking for datapoint matching " + device_id)
            for datapoint in datapoints["items"]:
                if datapoint["dataPointName"] == self.datapoint_name:
                    self.module.debug("Datapoint match found")
                    return datapoint
            self.module.debug("No datapoint match found")
            self.module.fail_json(
                msg="Error: No datapoint found with the provided name: {}".format(self.datapoint_name), changed=self.change, failed=True)
        self.module.debug("REST API call failed")
        self.change = False
        self.module.fail_json(
            msg="Error: unable to get the datapoints " +
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

    module_args = dict(
        company=dict(required=True, default=None),
        access_id=dict(required=True, default=None),
        access_key=dict(required=True, default=None, no_log=True),

        device_displayname=dict(required=True, default=None),
        datasource_displayname=dict(required=True, default=None),
        instance_name=dict(required=True, default=None),
        datapoint_name=dict(required=False, default=None),
        alert_disable=dict(required=False, default="false"),
        threshold=dict(required=False, default=None)
    )

    result = dict(
        changed=False,
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    target = Tuning(module.params, module)

    output = target.alert_threshold_tuning()

    result["changed"] = True
    result["message"] = output
    module.exit_json(**result)


if __name__ == "__main__":
    main()

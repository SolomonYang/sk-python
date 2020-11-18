# Author: Suresh Kanagala
#   sureshk@arista.com
#
# Script aimed for SR demos

import paramiko
from paramiko import client
import re
import json
import requests
import yaml
import random
import tkinter as tk
from Tkinter import *
import jsonrpclib
from jsonrpclib import Server
import schedule
import time
import threading
import dict
# import ssh
with open("inputs.yaml", 'r') as data:
    # input_vars = yaml.load(data)
    input_vars = yaml.load(data,Loader=yaml.FullLoader)
    # yaml.load(input, Loader=yaml.FullLoader)

from paramiko.ssh_exception import BadHostKeyException, AuthenticationException, SSHException
#---------------- Loading SSH for interaction with server ---------------#

ssh = paramiko.SSHClient()
ssh.load_system_host_keys()

#---------------- Connecting to EOS via eAPI ---------------#
pe1_conn = Server("http://cvpadmin:arista123@"+input_vars['pe1']+"/command-api")
lsr2_conn = Server("http://cvpadmin:arista123@"+input_vars['lsr2']+"/command-api")


#---------------- Establishing Connectivity to Controller APIs ---------------#
yabgp_url = "http://"+input_vars['yabpg_ip']+":8801/v1/peer/"+input_vars['pe1']+"/send/update"
sflowrt_url="http://"+input_vars['sflow_rt_ip']+":8008"

#---------------- JSON Headers for sFlow ---------------#
app_headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
MainFlow = {'keys': 'ipdestination', 'value': 'bytes'}


def push_seglist(color, user_input):
    color_attr = {}
    color_input = color
    user_input = user_input.split(' ')
    color_attr["1"] = [{"1": {"label": int(user_input[0])}}]
    for items in user_input[1:]:
        color_attr['1'].append({'1': {'label': int(items)}})
    payload = {}
    binding_sid = random.randint(965536, 1031071)
    payload['attr'] = {"1": 0, "2": [[2, [65000]]], "5": 100, "8": ["NO_ADVERTISE"], "14": {"afi_safi": [1, 73], "nexthop": input_vars['next_hop'], "nlri": {"distinguisher": 1002,
                                                                                                                                                             "color": color_input, "endpoint": input_vars['endpoint']}}, "23": {"0": "new", "12": 100, "13": binding_sid, "128": [{"9": 1, "1": color_attr['1']}]}}
    payload = json.dumps(payload)
    r = requests.post(yabgp_url, data=payload, headers=app_headers, auth=('admin', 'admin'))

def get_color():
    topflow = requests.get(sflowrt_url+'/activeflows/ALL/MainFlow/json?maxFlows=1')
    toptalker_dest = topflow.json()
    toptalker_dest = toptalker_dest[0]['key']
    toptalker_prefix = toptalker_dest.split('.')
    toptalker_prefix[-1] = '0'
    toptalker_prefix = '.'.join(toptalker_prefix)
    output = pe1_conn.runCmds(
        1, ['enable', 'show ip bgp '+toptalker_prefix+' | grep Color'], 'text')
    color = re.findall(".*Color:CO.*:(\d+)", output[1]['output'])[0]
    return [color, toptalker_prefix]

def runCmds(cmd_server):
    ssh.load_system_host_keys()
    ssh.connect(input_vars['sflow_rt_ip'], username='arista', password='arastra')
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd_server)
    time.sleep(5)  # optional 5 second pause for APIs to kick in
    flow = {'keys': 'ipdestination',
            'value': 'bytes', 'log': True}
    r = requests.put(sflowrt_url+'/flow/MainFlow/json', data=json.dumps(flow))
    r.connection.close()

def run_script():
    runCmds("sh sflow-rt/start.sh")
    requests.put(sflowrt_url+'/flow/MainFlow/json', data=json.dumps(MainFlow))
    output = lsr2_conn.runCmds(1, ['enable', 'show interfaces et5/1 counters rates'])
    linerate = round(output[1]['interfaces']['Ethernet5/1']['inPktsRate'])
    if linerate < 85:
        threading.Timer(1.0, run_script).start()
    else:
        time.sleep(4)
        print("\33[91m"+"\nCongestion Event Detected: Linerate on Et5/1 > 85 percent")
        time.sleep(2)
        print("\33[91m"+"....\n"+"\033[0m")
        print("\33[91m"+"Identifying the top-flow..."+"\033[0m")
        print("\33[91m"+"....\n"+"\033[0m")
        time.sleep(1)
        top_color = get_color()
        print("\33[91m"+"The top flow is destined to the prefix %s and has color %s" %
              (top_color[1], top_color[0])+"\033[0m")
        val = input("Enter the alternate segment list for top-talker (provide spaces between labels): ")
        
        push_seglist(int(top_color[0]), val)
        time.sleep(5)
run_script()

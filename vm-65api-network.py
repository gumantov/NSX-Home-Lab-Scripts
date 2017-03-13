import requests
import ast
import json

def get_value(list1, key):
    for subVal in list1:
        if subVal['name'] == vm_name:
            vm_id = subVal['vm']
            print vm_id
            return vm_id


username = "administrator@vsphere.local"
password = "VMware1!"
r = requests.post('https://vcsa-nsx.guslab.jumpingcrab.com/rest/com/vmware/cis/session', auth=(username, password), verify=False)
dict_r = ast.literal_eval(r.text)
session_id = dict_r['value']
headers = {'vmware-api-session-id': session_id}
print session_id
vm = requests.get('https://vcsa-nsx.guslab.jumpingcrab.com/rest/vcenter/vm', headers=headers, verify=False)
print vm.text
print type(vm.text)
vm_dict = json.loads(vm.text)
vm_list = vm_dict['value']
print vm_list
vm_name = raw_input('VM Name?')
vm_id = get_value(vm_list, vm_name)
print "this is the " + vm_id
vnic_number = requests.get('https://vcsa-nsx.guslab.jumpingcrab.com/rest/vcenter/vm/%s/hardware/ethernet'% (vm_id), headers=headers, verify=False)
vnicnum = json.loads(vnic_number.text)
print ((vnicnum['value'])[0])['nic']

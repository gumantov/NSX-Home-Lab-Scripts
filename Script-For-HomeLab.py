from nsxramlclient.client import NsxClient
import pprint
import ConfigParser
from pynsxv.library.nsx_logical_switch import *
from pynsxv.library.nsx_dlr import *
from pynsxv.library.nsx_esg import *
from pynsxv.library.nsx_dfw import *
from pynsxv.library.nsx_lb import *
from pynsxv.library.libutils import *
import json
import requests
import urllib2, base64

#credentials to connect to NSX Manager
nsx_manager = "192.168.1.21"
nsx_username = "admin"
nsx_password = "VMware1!"
tz = ''

nsxraml_file = 'nsxraml/nsxvapi.raml'
client_session = NsxClient(nsxraml_file, nsx_manager, nsx_username, nsx_password)

def get_transport_zone_name(tz):
	tz = client_session.read('vdnScopes', 'read')['body']
	vdnScopes = tz['vdnScopes']
	vdnScope = vdnScopes['vdnScope']
	tz_name = vdnScope['name']
	return tz_name


def logical_switch_create(client_session, transport_zone, logical_switch_name, control_plane_mode=None):
    """
    This function will create a new logical switch in NSX
    :param client_session: An instance of an NsxClient Session
    :param transport_zone: The name of the Scope (Transport Zone)
    :param logical_switch_name: The name that will be assigned to the new logical switch
    :param control_plane_mode: (Optional) Control Plane Mode, uses the Transport Zone default if not specified
    :return: returns a tuple, the first item is the logical switch ID in NSX as string, the second is string
             containing the logical switch URL location as returned from the API
    """
    vdn_scope_id, vdn_scope = get_scope(client_session, transport_zone)
    assert vdn_scope_id, 'The Transport Zone you defined could not be found'
    if not control_plane_mode:
        control_plane_mode = vdn_scope['controlPlaneMode']

    # get a template dict for the lswitch create
    lswitch_create_dict = client_session.extract_resource_body_example('logicalSwitches', 'create')

    # fill the details for the new lswitch in the body dict
    lswitch_create_dict['virtualWireCreateSpec']['controlPlaneMode'] = control_plane_mode
    lswitch_create_dict['virtualWireCreateSpec']['name'] = logical_switch_name
    lswitch_create_dict['virtualWireCreateSpec']['tenantId'] = ''

    # create new lswitch
    new_ls = client_session.create('logicalSwitches', uri_parameters={'scopeId': vdn_scope_id},
                                   request_body_dict=lswitch_create_dict)
    return new_ls['body'], new_ls['location']

def logical_switch_read(client_session, logical_switch_name):
    """
    This funtions retrieves details of a logical switch in NSX
    :param client_session: An instance of an NsxClient Session
    :param logical_switch_name: The name of the logical switch to retrieve details from
    :return: returns a tuple, the first item is a string containing the logical switch ID, the second is a dictionary
             containing the logical switch details retrieved from the API
    """
    logical_switch_id, logical_switch_params = get_logical_switch(client_session, logical_switch_name)
    return logical_switch_id, logical_switch_params

def dlr_list(client_session):
    """
    This function returns all DLR found in NSX
    :param client_session: An instance of an NsxClient Session
    :return: returns a tuple, the first item is a list of tuples with item 0 containing the DLR Name as string
             and item 1 containing the dlr id as string. The second item contains a list of dictionaries containing
             all DLR details
    """

    all_dist_lr = client_session.read_all_pages('nsxEdges', 'read')
    dist_lr_list = []
    dist_lr_list_verbose = []
    for dlr in all_dist_lr:
        if dlr['edgeType'] == "distributedRouter":
            dist_lr_list.append((dlr['name'], dlr['objectId']))
            dist_lr_list_verbose.append(dlr)
    return dist_lr_list, dist_lr_list_verbose

def dlr_read(client_session, dlr_name):
    """
    This funtions retrieves details of a dlr in NSX
    :param client_session: An instance of an NsxClient Session
    :param dlr_name: The name of the dlr to retrieve details from
    :return: returns a tuple, the first item is a string containing the dlr ID, the second is a dictionary
             containing the dlr details retrieved from the API
    """
    dlr_id, dlr_params = get_edge(client_session, dlr_name)
    return dlr_id, dlr_params

def dlr_add_interface(client_session, dlr_id, interface_ls_id, interface_ip, interface_subnet):
    """
    This function adds an interface gw to one dlr
    :param dlr_id: dlr uuid
    :param interface_ls_id: new interface logical switch
    :param interface_ip: new interface ip address
    :param interface_subnet: new interface subnet
    """

    # get a template dict for the dlr interface
    dlr_interface_dict = client_session.extract_resource_body_example('interfaces', 'create')

    # add default gateway to the created dlr if dgw entered
    dlr_interface_dict['interfaces']['interface']['addressGroups']['addressGroup']['primaryAddress'] = interface_ip
    dlr_interface_dict['interfaces']['interface']['addressGroups']['addressGroup']['subnetMask'] = interface_subnet
    dlr_interface_dict['interfaces']['interface']['isConnected'] = "True"
    dlr_interface_dict['interfaces']['interface']['connectedToId'] = interface_ls_id

    dlr_interface = client_session.create('interfaces', uri_parameters={'edgeId': dlr_id},
                                          query_parameters_dict={'action': "patch"},
                                          request_body_dict=dlr_interface_dict)
    return dlr_interface

def main():
	logical_switch_name = raw_input('Name your Switch:')
	transport_zone = get_transport_zone_name(tz)
	print "The name of my transport zone is" + " " + transport_zone
	logical_switch_create(client_session, transport_zone, logical_switch_name, control_plane_mode=None)
	dlr_list_get_name = dlr_list(client_session)
	dlr_id_found = dlr_list_get_name[0][0][1]
	run_ls_read = logical_switch_read(client_session, logical_switch_name)
	interface_ls_id = run_ls_read[0]
	print "Now we're creating an interface on DLR to connect to  your Logical Switch."
	interface_ip = raw_input('Give your interface an IP: ')
	interface_subnet = raw_input('Give your interface a Subnet: ')
	dlr_add_interface(client_session, dlr_id_found, interface_ls_id, interface_ip, interface_subnet)
	print "Interface was created successfuly"




if __name__ == "__main__":
	main()

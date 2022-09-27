#*- coding: utf-8 -*-
import csv
import re
import os
import configparser
import requests
import pymarc
import sys
import json
import threading
import time

okapi_url = None

#Creates the folder if it does not already exist
def check_or_create_dir(path):
    if not os.path.exists(path):
        if not os.path.exists(os.path.dirname(path)):
            check_or_create_dir(os.path.dirname(path))
        os.mkdir(path)


class configuration:
    def __init__(self):
        self.config_folder = os.path.join(os.path.join(os.path.join(os.path.join('C:\\Users', os.getlogin()), 'AppData'), 'Local'), 'FOLIO-api')
        check_or_create_dir(self.config_folder)
        if not os.path.isfile(self.config_folder):
            self.initial_config()
            self.add_section('data')
        else:
            self.initial_config()
        
    def initial_config(self):
        self.config = configparser.ConfigParser()
        self.config_file = os.path.join(self.config_folder, 'okapi_manager.ini')
        self.config_data = {}
        self.read_config_file()

    #
    def read_config_file(self):
        check_or_create_dir(self.config_folder)
        # create a blank file if none exists
        if not os.path.isfile(self.config_file):
            self.write_config_file()
        self.config.read(self.config_file)
    #Updates the configuration file with the current configuration
    def write_config_file(self):
        with open(self.config_file, 'w') as config_out:
            self.config.write(config_out)
    #Check to see if a section with a given name exist.
    def section_exist(self, section):
        if section in self.config:
            return True
        return False
    
    def add_section(self, section):
        if not self.section_exist(section):
            self.config[section] = {}
            self.write_config_file()
    

config = configuration()

def get_okapi_url_from_user():
    okapi_url = input('Okapi url:  ')
    return okapi_url

def get_tenant_from_user():
    tenant = input('Tenant:  ')
    return tenant

def get_username_from_user():
    username = input('Username:  ')
    return username

def get_password_from_user():
    password = input('Password:  ')
    return password

def get_uuid_from_user():
    uuid = input('UUID:  ')
    return uuid


def auth(change_okapi_url=False, change_tenant=False, change_username=False, change_password=False, refresh_token=False):
    global okapi_url
    okapi_url='https://okapi-crl.folio.ebsco.com'
    url = okapi_url + '/authn/login'
    if change_okapi_url or change_tenant or change_tenant or change_username or change_password or refresh_token or'tenant' not in config.config['data'] or 'username' not in config.config['data'] or 'password' not in config.config['data'] or 'okapi_token' not in config.config['data']:
        if change_okapi_url or 'okapi_url' not in config.config['data']:
            config.config['data']['okapi_url'] = get_okapi_url_from_user()
        if change_tenant or 'tenant' not in config.config['data']:
            config.config['data']['tenant'] = get_tenant_from_user()
        if change_username or 'username' not in config.config['data']:
            config.config['data']['username'] = get_username_from_user()
        if change_password or 'password' not in config.config['data']:
            config.config['data']['password'] = get_password_from_user()
        data = '{\"tenant\" : \"' + config.config['data']['tenant'] + '\", \"username\" : \"' + config.config['data']['username'] + '\", \"password\" : \"' + config.config['data']['password'] + '\"}'
        headers = {'Content-type' : 'application/json', 'X-Okapi-Tenant' : config.config['data']['tenant']}
        if refresh_token or 'okapi_token' not in config.config['data']:
            req = requests.post(url, data=data, headers=headers)
            config.config['data']['okapi_token'] = req.json()['okapiToken']
        config.write_config_file()

#Checks auth on start up.
auth()

#Replaces slash with space.
def replace_slash(text):
    while re.match('([^\\\]*)(\\\)(.*$)', text):
        text = re.match('([^\\\]*)(\\\)(.*$)', text).group(1) + ' ' + re.match('([^\\\]*)(\\\)(.*$)', text).group(3)
    return text

#Converts list to string.
def list_to_string(data):
    output = ''
    if type(data) is list:
        for item in data:
            output = output + item
    else:
        output = data
    return output

#Print completion status to screen.
def print_status(current, last):
    i = current / last
    i = "{:.1%}".format(i)
    sys.stdout.write('\r{0} complete.  Record {1} of {2}'.format(i, current, last))
    sys.stdout.flush()

#Formats 006 field dictionary into string
def format_006(data):
    formatted_006 = ''
    #Books
    if data['Type'] in ['t', 'a']:
        formatted_006 = list_to_string(data['Type']) + list_to_string(data['Ills']) + list_to_string(data['Audn']) + list_to_string(data['Form']) + list_to_string(data['Cont']) + list_to_string(data['GPub']) + list_to_string(data['Conf']) + list_to_string(data['Fest']) + list_to_string(data['Indx']) + ' ' + list_to_string(data['LitF']) + list_to_string(data['Biog'])
    #Continuing Resources
    elif data['Type'] == 's':
        formatted_006 = list_to_string(data['Type']) + list_to_string(data['Freq']) + list_to_string(data['Regl']) + ' ' + list_to_string(data['SrTp']) + list_to_string(data['Orig']) + list_to_string(data['Form']) + list_to_string(data['EntW']) + list_to_string(data['Cont']) + list_to_string(data['GPub']) + list_to_string(data['Conf']) + ' ' + ' ' + ' ' + list_to_string(data['Alph']) + list_to_string(data['S/L'])
    #Computer Files
    elif data['Type'] == 'm':
        formatted_006 = list_to_string(data['Type']) + ' ' + ' ' + ' ' + ' ' + list_to_string(data['Audn']) + list_to_string(data['Form']) + ' ' + ' ' + list_to_string(data['File']) + ' ' + list_to_string(data['GPub']) + ' ' + ' ' + ' ' + ' ' + ' ' + ' '
    #Maps
    elif data['Type'] in ['e', 'f']:
        formatted_006 = list_to_string(data['Type']) + list_to_string(data['Relf']) + list_to_string(data['Proj']) + ' ' + list_to_string(data['CrTp']) + ' ' + ' ' + list_to_string(data['GPub']) + list_to_string(data['Form']) + ' ' + list_to_string(data['Indx']) + ' ' + list_to_string(data['SpFm'])
    #Mixed Materials
    elif data['Type'] == 'p':
        formatted_006 = list_to_string(data['Type']) + ' ' + ' ' + ' ' + ' ' + ' ' + list_to_string(data['Form']) + ' ' + ' ' + ' ' + ' ' + ' ' + ' ' + ' ' + ' ' + ' ' + ' ' + ' '
    #Sound Recordings
    elif data['Type'] in ['i', 'j']:
        formatted_006 = list_to_string(data['Type']) + list_to_string(data['Comp']) + list_to_string(data['FMus']) + list_to_string(data['Part']) + list_to_string(data['Audn']) + list_to_string(data['Form']) + list_to_string(data['AccM']) + list_to_string(data['LTxt']) + ' ' + list_to_string(data['TrAr']) + ' '
        pass
    #Scores
    elif data['Type'] in ['c', 'd']:
        formatted_006 = list_to_string(data['Type']) + list_to_string(data['Comp']) + list_to_string(data['FMus']) + list_to_string(data['Part']) + list_to_string(data['Audn']) + list_to_string(data['Form']) + list_to_string(data['AccM']) + list_to_string(data['LTxt']) + ' ' + list_to_string(data['TrAr']) + ' '
    #Visual Materials
    elif data['Type'] in ['g', 'k', 'o', 'r']:
        formatted_006 = list_to_string(data['Type']) + list_to_string(data['Time']) + ' ' + list_to_string(data['Audn']) + ' ' + ' ' + ' ' + ' ' + ' ' + list_to_string(data['GPub']) + list_to_string(data['Form']) + ' ' + ' ' + ' ' + list_to_string(data['TMat']) + list_to_string(data['Tech'])
    formatted_006 = replace_slash(formatted_006)
    return formatted_006


#Formats 007 field dictionary into string
def format_007(data):
    formatted_007 = ''
    #Electronic Resource
    if data['$categoryName'].lower() == 'electronic resource':
        formatted_007 = list_to_string(data['Category']) + list_to_string(data['SMD']) + ' ' + list_to_string(data['Color']) + list_to_string(data['Dimensions']) + list_to_string(data['Sound']) + list_to_string(data['Image bit depth']) + list_to_string(data['File formats']) + list_to_string(data['Quality assurance target(s)']) + list_to_string(data['Antecedent/ Source']) + list_to_string(data['Level of compression']) + list_to_string(data['Reformatting quality'])
    #Globe
    elif data['$categoryName'].lower() == 'globe':
        formatted_007 = list_to_string(data['Category']) + list_to_string(data['SMD']) + ' ' + list_to_string(data['Color']) + list_to_string(data['Physical medium']) + list_to_string(data['Type of reproduction'])
    #Kit
    elif data['$categoryName'].lower() == 'kit':
        formatted_007 = list_to_string(data['Category']) + list_to_string(data['SMD'])
    #Map
    elif data['$categoryName'].lower() == 'map':
        formatted_007 = list_to_string(data['Category']) + list_to_string(data['SMD']) + ' ' + list_to_string(data['Color']) + list_to_string(data['Physical medium']) + list_to_string(data['Type of reproduction']) + list_to_string(data['Production/reproduction details']) + list_to_string(data['Positive/negative aspect'])
    #Microform
    elif data['$categoryName'].lower() == 'microform':
        formatted_007 = list_to_string(data['Category']) + list_to_string(data['SMD']) + ' ' + list_to_string(data['Positive/negative aspect']) + list_to_string(data['Dimensions']) + list_to_string(data['Reduction ratio range/Reduction ratio']) + list_to_string(data['Color']) + list_to_string(data['Emulsion on film']) + list_to_string(data['Generation']) + list_to_string(data['Base of film'])
    #Motion Picture
    elif data['$categoryName'].lower() == 'motion picture':
        formatted_007 = list_to_string(data['Category']) + list_to_string(data['SMD']) + ' ' + list_to_string(data['Color']) + list_to_string(data['Motion picture presentation format']) + list_to_string(data['Sound on medium or separate']) + list_to_string(data['Medium for sound']) + list_to_string(data['Dimensions']) + list_to_string(data['Configuration of playback channels']) + list_to_string(data['Production elements']) + list_to_string(data['Positive/Negative aspect']) + list_to_string(data['Generation']) + list_to_string(data['Base of film']) + list_to_string(data['Refined categories of color']) + list_to_string(data['Kind of color stock or print']) + list_to_string(data['Deterioration stage']) + list_to_string(data['Completeness']) + list_to_string(data['Film inspection date'])
    #Nonprojected Graphic
    elif data['$categoryName'].lower() == 'nonprojected graphic':
        formatted_007 = list_to_string(data['Category']) + list_to_string(data['SMD']) + ' ' + list_to_string(data['Color']) + list_to_string(data['Primary support material']) + list_to_string(data['Secondary support material'])
        pass
    #Notated Music
    elif data['$categoryName'].lower() == 'notated music':
        formatted_007 = list_to_string(data['Category']) + list_to_string(data['SMD'])
        pass
    #Projected Graphic
    elif data['$categoryName'].lower() == 'projected graphic':
        formatted_007 = list_to_string(data['Category']) + list_to_string(data['SMD']) + ' ' + list_to_string(data['Color']) + list_to_string(data['Color']) + list_to_string(data['Base of emulsion']) + list_to_string(data['Sound on medium or separate']) + list_to_string(data['Medium for sound']) + list_to_string(data['Dimensions']) + list_to_string(data['Secondary support material'])
        pass
    #Remote-sensing Image
    elif data['$categoryName'].lower() == 'remote-sensing image':
        formatted_007 = list_to_string(data['Category']) + list_to_string(data['SMD']) + ' ' + list_to_string(data['Altitude of sensor']) + list_to_string(data['Attitude of sensor']) + list_to_string(data['Cloud cover']) + list_to_string(data['Platform construction type']) + list_to_string(data['Platform use category']) + list_to_string(data['Sensor type']) + list_to_string(data['Data type'])
        pass
    #Sound Recording
    elif data['$categoryName'].lower() == 'sound recording':
        formatted_007 = list_to_string(data['Category']) + list_to_string(data['SMD']) + ' ' + list_to_string(data['Speed']) + list_to_string(data['Configuration of playback channels']) + list_to_string(data['Groove width/ groove pitch']) + list_to_string(data['Dimensions']) + list_to_string(data['Tape width']) + list_to_string(data['Tape configuration']) + list_to_string(data['Kind of disc, cylinder, or tape']) + list_to_string(data['Kind of material']) + list_to_string(data['Kind of cutting']) + list_to_string(data['Special playback characteristics']) + list_to_string(data['Capture and storage technique'])
        pass
    #Tactile Material
    elif data['$categoryName'].lower() == 'tactile material':
        formatted_007 = list_to_string(data['Category']) + list_to_string(data['SMD']) + ' ' + list_to_string(data['Class of braille writing']) + list_to_string(data['Level of contraction']) + list_to_string(data['Braille music format']) + list_to_string(data['Special physical characteristics'])
        pass
    #Text
    elif data['$categoryName'].lower() == 'text':
        formatted_007 = list_to_string(data['Category']) + list_to_string(data['SMD'])
    #Unspecified
    elif data['$categoryName'].lower() == 'unspecified':
        formatted_007 = list_to_string(data['Category']) + list_to_string(data['SMD'])
        pass
    #Videorecording
    elif data['$categoryName'].lower() == 'videorecording':
        formatted_007 = list_to_string(data['Category']) + list_to_string(data['SMD']) + ' ' + list_to_string(data['Color']) + list_to_string(data['Videorecording format']) + list_to_string(data['Sound on medium or separate']) + list_to_string(data['Medium for sound']) + list_to_string(data['Dimensions']) + list_to_string(data['Configuration of playback channels'])
        pass
    formatted_007 = replace_slash(formatted_007)
    return formatted_007

#Formats 008 field dictionary into string
def format_008(data):
    formatted_008 = ''
    field_008_start = list_to_string(data['Entered']) + list_to_string(data['DtSt']) + list_to_string(data['Date1']) + list_to_string(data['Date2']) + list_to_string(data['Ctry'])
    field_008_end = list_to_string(data['Lang']) + list_to_string(data['MRec']) + list_to_string(data['Srce'])
    #Books
    if data['Type'] == 't' or (data['Type'] == 'a' and data['BLvl'] in ['a', 'c', 'd', 'm']):
        field_008_middle = list_to_string(data['Ills']) + list_to_string(data['Audn']) + list_to_string(data['Form']) + list_to_string(data['Cont']) + list_to_string(data['GPub']) + list_to_string(data['Conf']) + list_to_string(data['Fest']) + list_to_string(data['Indx']) + ' ' + list_to_string(data['LitF']) + list_to_string(data['Biog'])
    #Continuing Resources
    elif data['Type'] == 'a' and data['BLvl'] in ['b', 'i', 's']:
        field_008_middle = list_to_string(data['Freq']) + list_to_string(data['Regl']) + ' ' + list_to_string(data['SrTp']) + list_to_string(data['Orig']) + list_to_string(data['Form']) + list_to_string(data['EntW']) + list_to_string(data['Cont']) + list_to_string(data['GPub']) + list_to_string(data['Conf']) + ' ' + ' ' + ' ' + list_to_string(data['Alph']) + list_to_string(data['S/L'])
    #Computer Files
    elif data['Type'] == 'm':
        field_008_middle = ' ' + ' ' + ' ' + ' ' + list_to_string(data['Audn']) + list_to_string(data['Form']) + ' ' + ' ' + list_to_string(data['File']) + ' ' + list_to_string(data['GPub']) + ' ' + ' ' + ' ' + ' ' + ' ' + ' '
    #Maps
    elif data['Type'] == 'e' or data['Type'] == 'f':
        field_008_middle = list_to_string(data['Relf']) + list_to_string(data['Proj']) + ' ' + list_to_string(data['CrTp']) + ' ' + ' ' + list_to_string(data['GPub']) + list_to_string(data['Form']) + ' ' + list_to_string(data['Indx']) + ' ' + list_to_string(data['SpFm'])
    #Mixed Materials
    elif data['Type'] == 'p':
        field_008_middle = ' ' + ' ' + ' ' + ' ' + ' ' + list_to_string(data['Form']) + ' ' + ' ' + ' ' + ' ' + ' ' + ' ' + ' ' + ' ' + ' ' + ' ' + ' '
    #Sound Recordings
    elif data['Type'] == 'i' or data['Type'] == 'j':
        field_008_middle = list_to_string(data['Comp']) + list_to_string(data['FMus']) + list_to_string(data['Part']) + list_to_string(data['Audn']) + list_to_string(data['Form']) + list_to_string(data['AccM']) + list_to_string(data['LTxt']) + ' ' + list_to_string(data['TrAr']) + ' '
    #Scores
    elif data['Type'] == 'c' or data['Type'] == 'd':
        field_008_middle = list_to_string(data['Comp']) + list_to_string(data['FMus']) + list_to_string(data['Part']) + list_to_string(data['Audn']) + list_to_string(data['Form']) + list_to_string(data['AccM']) + list_to_string(data['LTxt']) + ' ' + list_to_string(data['TrAr']) + ' '
    #Visual Materials
    elif data['Type'] == 'g' or data['Type'] == 'k' or data['Type'] == 'o' or data['Type'] == 'r':
        field_008_middle = list_to_string(data['Time']) + ' ' + list_to_string(data['Audn']) + ' ' + ' ' + ' ' + ' ' + ' ' + list_to_string(data['GPub']) + list_to_string(data['Form']) + ' ' + ' ' + ' ' + list_to_string(data['TMat']) + list_to_string(data['Tech'])
    formatted_008 = replace_slash(field_008_start + field_008_middle + field_008_end)
    return formatted_008

#Converts record from json to marc then returns record.
def get_marc(uuid = None):
    global okapi_url
    if uuid is None:
        uuid = get_uuid_from_user()
    headers = {'Accept' : 'application/json', 'X-Okapi-Tenant' : config.config['data']['tenant'], 'x-okapi-token' : config.config['data']['okapi_token']}
    url = okapi_url + '/records-editor/records?externalId=' + uuid
    req = requests.get(url, headers=headers)
    json_record = req.json()
    record = pymarc.Record()
    record.leader = replace_slash(json_record['leader'])
    row_006 = None
    for row in json_record['fields']:
        tag = row['tag']
        if int(row['tag']) < 10:
            if int(row['tag']) in [6, 7, 8]:
                if int(row['tag']) == 6:
                    row['content'] = format_006(row['content'])
                if int(row['tag']) == 7:
                    row['content'] = format_007(row['content'])
                if int(row['tag']) == 8:
                    row['content'] = format_008(row['content'])
            record.add_field(pymarc.Field(row['tag'], data=row['content']))
        else:
            subfields = []
            for match in re.finditer('(?:\$)([^\$])([^\$]+)', row['content']):
                subfields.append(match.group(1))
                subfields.append(match.group(2))
            record.add_field(pymarc.Field(row['tag'], row['indicators'], subfields))
    print()
    print(record)
    return record

#Gets iterable of all the instance records.
def get_instance_records_all(start = 0, limit = 10000, return_type = 'json'):
    global okapi_url
    headers = {'Accept' : 'application/json', 'X-Okapi-Tenant' : config.config['data']['tenant'], 'x-okapi-token' : config.config['data']['okapi_token']}
    url = okapi_url + '/instance-storage/instances'
    a = start
    params = {'limit' : '1'}
    req = requests.get(url, params=params, headers=headers)
    json_record = req.json()
    end = json_record['totalRecords']
    while start < end:
        params = {'offset' : str(start), 'limit' : str(limit)}
        req = requests.get(url, params=params, headers=headers)
        json_record = req.json()
        for instance_record in json_record['instances']:
            if return_type == 'text':
                yield req.text
            else:
                yield req.json()
            a += 1
            print_status(a, end)
        start += 10000

#Gets iterable of all the marc records.
def get_marc_records_all(start = 333129, limit = 10000, return_type = 'marc'):
    global okapi_url
    headers = {'Accept' : 'application/json', 'X-Okapi-Tenant' : config.config['data']['tenant'], 'x-okapi-token' : config.config['data']['okapi_token']}
    url = okapi_url + '/instance-storage/instances'
    a = start
    params = {'limit' : '1'}
    req = requests.get(url, params=params, headers=headers)
    json_record = req.json()
    end = json_record['totalRecords']
    while start <= end:
        params = {'offset' : str(start), 'limit' : str(limit)}
        req = requests.get(url, params=params, headers=headers)
        json_record = req.json()
        for instance_record in json_record['instances']:
            if return_type == 'text':
                yield req.text
            elif return_type == 'json':
                yield req.json()
            else:
                marc_record = get_marc(uuid = instance_record['id'])
                yield marc_record
            a += 1
            print_status(a, end)
        start += limit

#Gets instance_record.
def get_instance_record(uuid = None, return_type = 'json'):
    global okapi_url
    if uuid is None:
        uuid = get_uuid_from_user()
    headers = {'Accept' : 'application/json', 'X-Okapi-Tenant' : config.config['data']['tenant'], 'x-okapi-token' : config.config['data']['okapi_token']}
    if uuid != '' and uuid is not None:
        url = okapi_url + '/instance-storage/instances/' + uuid
        req = requests.get(url, headers=headers)
    else:
        url = okapi_url + '/instance-storage/instances?limit=0'
        req = requests.get(url, headers=headers)
    if return_type == 'text':
        return req.text
    elif return_type == 'json':
        return req.json()
    else:
        return None

#Gets holding records from instance_id.
def get_holding_records_from_instance_id(uuid = None, return_type = 'json'):
    global okapi_url
    if uuid is None:
        uuid = get_uuid_from_user()
    headers = {'Accept' : 'application/json', 'X-Okapi-Tenant' : config.config['data']['tenant'], 'x-okapi-token' : config.config['data']['okapi_token']}
    if uuid != '' and uuid is not None:
        url = okapi_url + '/holdings-storage/holdings?limit=10000&query=instanceId==' + uuid
        req = requests.get(url, headers=headers)
    else:
        url = okapi_url + '/instance-storage/instances?limit=0'
        req = requests.get(url, headers=headers)
    if return_type == 'text':
        return req.text
    elif return_type == 'json':
        return req.json()
    else:
        return None

#Gets item records from instance_id.
def get_item_records_from_instance_id(uuid = None, return_type = 'json'):
    global okapi_url
    if uuid is None:
        uuid = get_uuid_from_user()
    headers = {'Accept' : 'application/json', 'X-Okapi-Tenant' : config.config['data']['tenant'], 'x-okapi-token' : config.config['data']['okapi_token']}
    if uuid != '' and uuid is not None:
        url = okapi_url + '/inventory/items?limit=10000&query=instance.id==' + uuid
        req = requests.get(url, headers=headers)
    else:
        url = okapi_url + '/instance-storage/instances?limit=0'
        req = requests.get(url, headers=headers)
    if return_type == 'text':
        return req.text
    else:
        return req.json()


#Gets holding records.
def get_holdings_record(uuid = None, return_type = 'json'):
    global okapi_url
    if uuid is None:
        uuid = get_uuid_from_user()
    while re.match('(.*)(?:[^a-f0-9\-]+)(.*$)', uuid):
        uuid = re.match('(.*)(?:[^a-f0-9\-]+)(.*$)', uuid).group(1) + re.match('(.*)(?:[^a-f0-9\-]+)(.*$)', uuid).group(2)
    headers = {'Accept' : 'application/json', 'X-Okapi-Tenant' : config.config['data']['tenant'], 'x-okapi-token' : config.config['data']['okapi_token']}
    print(uuid)
    if uuid != '' and uuid is not None:
        url = okapi_url + '/holdings-storage/holdings/' + uuid
        req = requests.get(url, headers=headers)
    else:
        url = okapi_url + '/holdings-storage/holdings?limit=0'
        params = {'limit': '0'}
        req = requests.get(url, params=params, headers=headers)
    if return_type == 'text':
        return req.text
    else:
        return req.json()


#Suppresses record.
def suppress_record(uuid = None):
    global okapi_url
    if uuid is None:
        uuid = get_uuid_from_user()
    while re.match('(.*)(?:[^a-f0-9\-]+)(.*$)', uuid):
        uuid = re.match('(.*)(?:[^a-f0-9\-]+)(.*$)', uuid).group(1) + re.match('(.*)(?:[^a-f0-9\-]+)(.*$)', uuid).group(2)
    headers = {'Content-type' : 'application/json', 'Accept' : 'text/plain', 'X-Okapi-Tenant' : config.config['data']['tenant'], 'x-okapi-token' : config.config['data']['okapi_token']}
    if uuid != '' and uuid is not None:
        url = okapi_url + '/instance-storage/instances/' + uuid
        req = requests.get(url, headers=headers)
        json_record = req.json()
        json_record['discoverySuppress'] = True
        data = json.dumps(json_record)
        print(uuid + ' suppressed')


#Gets iterable ofall the holding record ids.
def get_holdings_record_ids(start = 0, limit = 100000, return_type = 'json'):
    global okapi_url
    headers = {'Accept' : 'application/json', 'X-Okapi-Tenant' : config.config['data']['tenant'], 'x-okapi-token' : config.config['data']['okapi_token']}
    url = okapi_url + '/holdings-storage/holdings'
    a = start
    params = {'limit' : '1'}
    req = requests.get(url, params=params, headers=headers)
    json_record = req.json()
    end = json_record['totalRecords']
    while start <= end:
        params = {'offset' : str(start), 'limit' : str(limit)}
        req = requests.get(url, params=params, headers=headers)
        json_record = req.json()
        for holdings_record in json_record['holdingsRecords']:
            yield holdings_record['id']
            a += 1
            print_status(a, end)
        start += limit


if __name__=="__main__":
    file_direct = os.path.dirname(os.path.realpath('__file__'))
#    auth(change_okapi_url=True)
#    auth(change_username=True, change_tenant=True, change_okapi_url=True, change_password=True)
#    auth(refresh_token=True)
#    get_marc()
#    get_holdings_record()
#    get_holdings_record_ids()
#    for record in get_holdings_record_ids():
#        pass
#    get_instance_records_all()
#    for record in get_instance_records_all():
#        pass
#    suppress_record()
#    get_marc_records_all()
    for record in get_marc_records_all():
        pass


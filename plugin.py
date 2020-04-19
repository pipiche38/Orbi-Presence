# Basic Python Plugin Example
#
# Author: pipiche
#
"""
<plugin key="OrbiPresence" name="Presence on Orbi Router/AP" author="pipiche38" version="0.0.4" wikilink="http://www.domoticz.com/wiki/plugins/plugin.html" externallink="https://www.google.com/">
    <description>
        <h2>Presence on Orbi Router/AP</h2><br/>
        The plugin will check the presence or not of the entered Mac address, by checking against the Orbi Router list of Devices.

        <h3>Configuration</h3>
        Simply enter the list of Mac Address you want to monitor. They must be separater by coma.
        For each mac address a specific device will be created.
        When this mac is present the Switch will be On, otherwise Off

        You need to enter:
        the IP address of the orbi router (gateway)
        the username and password to access the router
    </description>
    <params>
        <param field="Mode4" label="list of Mac addresses" required="true" />
        <param field="Address" label="ip" width="150px" required="true" default="10.0.0.1"/>
        <param field="Username" label="Username" width="150px" required="true" />
        <param field="Password" label="Username" width="150px" required="true" password="true"/>
        <param field="Mode6" label="Verbors and Debuging" width="150px">
            <options>
                        <option label="None" value="0"  default="true"/>
                        <option label="Verbose" value="2"/>
                        <option label="Domoticz Framework - Basic" value="62"/>
                        <option label="Domoticz Framework - Basic+Messages" value="126"/>
                        <option label="Domoticz Framework - Connections Only" value="16"/>
                        <option label="Domoticz Framework - Connections+Queue" value="144"/>
                        <option label="Domoticz Framework - All" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz

import json
import sys
import re
sys.path.append('/usr/lib/python3.6/site-packages')
import requests
from requests.auth import HTTPBasicAuth

class BasePlugin:
    enabled = False
    def __init__(self):
        self.username = None
        self.password = None
        self.session = None

        self.macs = None
        self.ip = None
        return

    def onStart(self):
        Domoticz.Log("onStart called")
        Domoticz.Heartbeat(30)
        Domoticz.Log('Mode6: %s' %Parameters["Mode6"])
        Domoticz.Debugging(int(Parameters["Mode6"]))
        self.username = Parameters["Username"]
        self.password = Parameters["Password"]
        list_macs = (Parameters["Mode4"].strip()).split(',')
        self.macs = []
        self.ip = Parameters["Address"]
        list_device_mac = []
        homeicon = "idetect-home"
        homeiconid =  None
        Domoticz.Log("--> %s" %str(Images))
        if homeicon in Images: 
            homeiconid=Images[homeicon].ID
        else:
            Domoticz.Log("Uploading Orbi-Presence Icons")
            Domoticz.Image('ihome.zip').Create()
            homeiconid=Images[homeicon].ID

        Domoticz.Log("Images: %s" %str(Images))
        for img in Images:
            Domoticz.Log("Images: %s ==> Id: %s, Name: %s " %(img, Images[ img ].ID, Images[ img ].Name))

        Domoticz.Log("--> homeiconid: %s" %homeiconid)


        #Create "Anyone home" device
        if 1 not in Devices:
            Domoticz.Debug('Create Widget Anyone @ Home' )
            if homeiconid:
                myDev = Domoticz.Device(DeviceID='#Anyone', Name="Anyone@Home", Unit=1, TypeName="Switch", Used=1, Image=homeiconid)
            else:
                myDev = Domoticz.Device(DeviceID='#Anyone', Name="Anyone@Home", Unit=1, TypeName="Switch", Used=1)
            myDev.Create()

        for iterDev in Devices:
            list_device_mac.append(Devices[iterDev].DeviceID )
        Domoticz.Debug("List of Devices: %s" %str(list_device_mac))
        for iter in Parameters["Mode4"].split(','):
            mac = format_mac(iter)

            Domoticz.Status('- watching MAC@: %s' %mac)
            if mac not in list_device_mac:
                Domoticz.Debug('Create Widget for %s' %mac)
                myDev = Domoticz.Device(DeviceID=mac, Name=mac+" Presence", Unit=FreeUnit(Devices), Type=244)
                myDev.Create()
            self.macs.append(iter.strip(' '))
        Domoticz.Status("Connect to Orbi")
        self.session= requests.Session()
        self.session.auth = ( self.username, self.password )

    def onStop(self):
        Domoticz.Debug("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("onConnect called")

    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called")
        if not self.ip:
            return
        url = 'http://' +self.ip + "/DEV_device_info.htm"

        Domoticz.Debug("url to check : %s" %url)
        try:
            if self.session:
                r = self.session.get( url )
            else:
                r = requests.get(url, auth=HTTPBasicAuth(self.username, self.password))
            r.raise_for_status()
            
        except requests.exceptions.TooManyRedirects:
            Domoticz.Errors("URL was bad. %s" %url)
            return
        
        except requests.exceptions.ConnectionError as errc:
            Domoticz.Log("Error Connecting: %s - %s" %(url, errc))
            return
        
        except requests.exceptions.HTTPError as err:
            Domoticz.Error("Error on requests(%s): %s" %(url, err))
            return
        
        except requests.exceptions.Timeout:
            Domoticz.Error("Timeout on requests(%s)" %url)
            return
        
        except requests.exceptions.RequestException as e:
            Domoticz.Log("Catastophic error. %url - %s" %(url, e))

        if len(r.text) < 200:
            Domoticz.Error("response seems too short: %s - %s" %(url, r.text))
            return

        lines = r.text.split('\n')
        Domoticz.Debug("lines: %s" %lines)

        if len(lines) < 2:
            Domoticz.Error("Unexpected value (too short)) for lines: %s" %lines)
            return

        device = lines[1].split('=')
        if len(device) < 2:
            Domoticz.Error("Unexpected value (too short)) for device: %s" %device)
            return

        Domoticz.Debug("lines: %s" %lines)
        Domoticz.Debug("device: %s" %device)
        try:
            json_orbi = json.loads(device[1])
        except:
            Domoticz.Debug("looks like something went wrong with json.loads(%): device: %s" %device[1])
            return

        cnt = 0
        dico_orbi = {}
        for iter in json_orbi:
            dico_orbi[cnt] = {}
            dico_orbi[cnt] = iter
            cnt += 1

        mac_presence = []
        for iter in dico_orbi:
            if dico_orbi[iter]['mac'] in self.macs:
                mac_presence.append(format_mac(dico_orbi[iter]['mac']))
        Domoticz.Log('MAC@ present are : %s' %mac_presence)
        oneOn = False
        for iterDev in Devices:
            if iterDev == 1: continue
            if Devices[iterDev].DeviceID in mac_presence:
                oneOn = True
                Domoticz.Log('%s is at home' %Devices[iterDev].Name)
                if Devices[iterDev].sValue != 'On':
                    Devices[iterDev].Update(nValue=1, sValue='On')
            else:
                Domoticz.Log('%s is away' %Devices[iterDev].Name)
                if Devices[iterDev].sValue != 'Off':
                    Devices[iterDev].Update(nValue=0, sValue='Off')

        Domoticz.Log("@Home: %s %s, oneOn: %s" %(Devices[1].nValue, Devices[1].sValue, oneOn))

        if oneOn:
            if Devices[1].sValue != 'On':
                Domoticz.Log("Update Anyone@Home to On")
                Devices[1].Update(nValue=1, sValue='On')
        else:
            if Devices[1].sValue != 'Off':
                Domoticz.Log("Update Anyone@Home to Off")
                Devices[1].Update(nValue=0, sValue='Off')



global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return

def format_mac(mac: str) -> str:
    mac = re.sub('[.:-]', '', mac).upper()  # remove delimiters and convert to upper case
    mac = ''.join(mac.split())  # remove whitespaces
    assert len(mac) == 12  # length should be now exactly 12 (eg. 008041aefd7e)
    assert mac.isalnum()  # should only contain letters and numbers
    # convert mac in canonical form (eg. 00:80:41:ae:fd:7e)
    mac = ":".join(["%s" % (mac[i:i+2]) for i in range(0, 12, 2)])
    return mac


def FreeUnit( Devices, nbunit_=1):
    '''
    FreeUnit
    Look for a Free Unit number. If nbunit > 1 then we look for nbunit consecutive slots
    '''
    FreeUnit = ""
    for x in range(1, 255):
        if x not in Devices:
            if nbunit_ == 1:
                return x
            nb = 1
            for y in range(x+1, 255):
                if y not in Devices:
                    nb += 1
                else:
                    break
                if nb == nbunit_: # We have found nbunit consecutive slots
                    loggingWidget( self, "Debug", "FreeUnit - device " + str(x) + " available")
                    return x

    else:
        return len(Devices) + 1

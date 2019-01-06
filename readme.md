# Presence from Orbi Router

This little plugin allow to detect Mac Addresses presence by quering the Orbi Router

## Requirements 
This Plugin use the requests module. ( http://docs.python-requests.org/en/master/ ) on the current version the module is expected to be under the following folder /usr/lib/python3.6/site-packages'. If that is not your case in your current system, you'll have to update the plugin.py file accordingly


## Installation
1. Got to the plugin directory of Domoticz and execute the command:
   * git clone https://github.com/pipiche38/Orbi-Presence.git
1. Restart Domoticz
1. Got to Hardware
1. Add Hardware and select 'Presence on Orbi Router/AP'
   * Specify a Name
   * Provide a list of Mac address you want to monitor
   * Provide the IP address of your Orbi router/AP
   * Provide the Username and Password



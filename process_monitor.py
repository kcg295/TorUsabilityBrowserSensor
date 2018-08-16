#!/usr/bin/env python3
"""
File: process_monitor.py
Author: Kevin Gallagher
Email: kevin.gallagher@nyu.edu

Description:
The purpose of this program is to determine when a user switches from
Tor browser to another browser in order to determine the stop points of
the Tor Browser Bundle. To do this, this script will monitor the
process list of the client's machine for new instances of firefox,
chrome, safari, etc. When the browsing session is closed, the user will
be promopted to answer survey questions.
"""
import psutil
from sys import platform
import os
import configparser
import time

"""
The following imports are not necessary for the script, but are required
for the packaging into an application and creating the graphical
installer.
"""
if platform == "darwin":
    import six
    import packaging
    import packaging.version
    import packaging.specifiers
    import appdirs
    import packaging.requirements
    import _sysconfigdata_m_darwin_darwin

# This class contains flags that are used to decide whether or not a
# survey should be displayed to the user. These flags are populated
# through constant checks on the process list.
class BrowserState:
    def __init__(self):
        self.tor_state = False
        self.firefox_state = False
        self.safari_state = False
        self.chrome_state = False
        self.opera_state = False
        self.edge_state = False
        self.trigger_survey = False
        self.trigger_tor_survey = False
        self.NONTOR = 0
        self.SWITCHED = 1
        self.TOR = 2
        #self.first_run = True

    def firefox_running(self):
        self.firefox_state = True

    def chrome_running(self):
        self.chrome_state = True 

    def safari_running(self):
        self.safari_state = True

    def tor_running(self):
        self.tor_state = True
        #if not self.first_run and time.time() >= LASTSURVEY + 86400:
        #    self.trigger_tor_survey = True
        #self.first_run = False

    def opera_running(self):
        self.opera_state = True

    def edge_running(self):
        self.edge_state = True

    def firefox_off(self):
        if self.firefox_state:
            self.trigger_survey = True
        self.firefox_state = False

    def chrome_off(self):
        if self.chrome_state:
            self.trigger_survey = True
        self.chrome_state = False

    def safari_off(self):
        if self.safari_state:
            self.trigger_survey = True
        self.safari_state = False

    def tor_off(self):
        if self.tor_state:
            self.trigger_tor_survey = True
        self.tor_state = False

    def opera_off(self):
        if self.opera_state:
            self.trigger_survey = True
        self.opera_state = False

    def edge_off(self):
        if self.edge_state:
            self.trigger_survey = True
        self.edge_state = False

    def deactivate_survey(self):
        self.trigger_survey = False

    def deactivate_tor_survey(self):
        self.trigger_tor_survey = False

    def reset(self):
        self.tor_state = False
        self.firefox_state = False
        self.safari_state = False
        self.chrome_state = False
        self.opera_state = False
        self.edge_state = False
        self.trigger_survey = False
        self.trigger_tor_survey = False

# Step zero: check the platform and determine what the appropriate
# process check is depending on the results. Set the process_check
# funciton pointer to point to that function. In addition, after
# determining the platform we will load a unique identifier and 
# other information, such as the onion address of the server
# listening for submissions.
LASTSURVEY = 0
SLEEPTIME = 900 #Sleep for 15 minutes after browser is launched.
def main():
    # Step One: Declare the variables we will be using to indicate
    # whether certain browsers are running. Specifically, we will 
    # display a survey prompt when one of these variables go from True
    # to False, meaning that a browsing session has been closed. We
    # will keep track of this with the BrowserState class we wrote
    # earlier.
    browsers = BrowserState()

    print("Created Browser States. Now enetering Main Loop.")
    # Last step: enter the process checking loop. This loop will
    # determine which browsers are running, and based on browsers
    # opening and closing will decide to trigger the survey.
    found = {'firefox':False, 'tor':False, 'opera':False, 
            'safari':False, 'edge':False, 'chrome':False}
    while True:
        browsers, found = process_check(browsers, variables, found)
        if browsers.trigger_survey and not browsers.tor_state:
            print("Displaying nontor survey")
            display_survey(browsers, browsers.NONTOR,
                    tor_url, switched_url, non_tor_url)
            browsers.deactivate_survey()
        elif browsers.trigger_survey:
            print("Displaying switched survey")
            display_survey(browsers, browsers.SWITCHED,
                    tor_url, switched_url, non_tor_url)
            browsers.deactivate_survey()
            browsers.deactivate_tor_survey()
        elif browsers.trigger_tor_survey:
            print("Displaying Tor survey")
            display_survey(browsers, browsers.TOR,
                    tor_url, switched_url, non_tor_url)
            browsers.deactivate_tor_survey()

# The following function checks processes on Linux distributions. It 
# relies on the cmdline variables to distinguish the Tor Browser Bundle 
# from Firefox.
def ul_process_check(browsers, variables, found):
    firefox = variables['firefox']
    tor = variables['tor']
    chrome = variables['chrome']
    safari = variables['safari']
    opera = variables['opera']

    found_firefox = False
    found_tor = False
    found_chrome = False
    found_safari = False
    found_opera = False

    for proc in psutil.process_iter():
        try:
            proc = proc.as_dict()
       
            if proc['name'] is None:
                continue
            if (firefox['name'] in proc['name'] 
                and tor['cmdline'] not in str(proc['cmdline'])
                and not found_firefox):
                browsers.firefox_running()
                found['firefox'] = True
                found_firefox = True

            elif (chrome['name'] in proc['name']
                and chrome['cmdline'] not in str(proc['cmdline'])
                and not found_chrome):
                browsers.chrome_running()
                found['chrome'] = True
                found_chrome = True

            elif (safari['name'] in proc['name']
                and safari['cmdline'] in str(proc['cmdline'])
                and not found_safari):
                browsers.safari_running()
                found['safari'] = True
                found_safari = True

            elif (tor['name'] in proc['name']
                and tor['cmdline'] in str(proc['cmdline'])
                and not found_tor):
                browsers.tor_running()
                found['tor'] = True
                found_tor = True

            elif (opera['name'] in proc['name']
                and opera['cmdline'] not in str(proc['cmdline'])
                and not found_opera):
                browsers.opera_running()
                found['opera'] = True
                found_opera = True
        except psutil.NoSuchProcess as e:
            continue

    if not found_tor:
        browsers.tor_off()
        found['tor'] = False
    if not found_chrome:
        browsers.chrome_off()
        found['chrome'] = False
    if not found_safari:
        browsers.safari_off()
        found['safari'] = False
    if not found_firefox:
        browsers.firefox_off()
        found['firefox'] = False
    if not found_opera:
        browsers.opera_off()
        found['opera'] = False

    return browsers, found

# The following function checks processes on Mac OS. It relies on the 
# cmdline variables to distinguish the Tor Browser Bundle from Firefox.
# In addition, it checks to see if a current window is active for any 
# of the browser processes that it finds before assumming that a
# browser is open because of how Mac handles processes.
def mac_process_check(browsers, variables, found):
    firefox = variables['firefox']
    tor = variables['tor']
    chrome = variables['chrome']
    safari = variables['safari']
    opera = variables['opera']

    found_firefox = False
    found_tor = False
    found_chrome = False
    found_safari = False
    found_opera = False

    potentially_found = {}

    print("Going through processes.")
    for proc in psutil.process_iter():
        proc = proc.as_dict()
       
        if proc['name'] is None:
            continue
        if (firefox['name'] in proc['name'] 
            and tor['cmdline'] not in str(proc['cmdline'])
            and not found_firefox):
            print("Firefox potentiall found.")
            pid = proc['pid']
            potentially_found[pid] = 'firefox'

        elif (chrome['name'] in proc['name']
            and chrome['cmdline'] not in str(proc['cmdline'])
            and not found_chrome):
            pid = proc['pid']
            potentially_found[pid] = 'chrome'

        elif (safari['name'] in proc['name']
            and safari['cmdline'] in str(proc['cmdline'])
            and not found_safari):
            pid = proc['pid']
            potentially_found[pid] = 'safari'

        elif (tor['name'] in proc['name']
            and tor['cmdline'] in str(proc['cmdline'])
            and not found_tor):
            pid = proc['pid']
            potentially_found[pid] = 'tor'

        elif (opera['name'] in proc['name']
            and opera['cmdline'] not in str(proc['cmdline'])
            and not found_opera):
            pid = proc['pid']
            potentially_found[pid] = 'opera'

    windows = Quartz.CGWindowListCopyWindowInfo(
                Quartz.kCGWindowListOptionAll,
                Quartz.kCGNullWindowID)

    potential_firefox_windows = []
    potential_chrome_windows = []
    potential_safari_windows = []
    potential_tor_windows = []
    potential_opera_windows = []
    for window in windows:
        window_pid = window.valueForKey_('kCGWindowOwnerPID')
        try:
            browser_name = potentially_found[window_pid]
        except KeyError:
            continue
        if browser_name == 'firefox':
            potential_firefox_windows.append(window)
        elif browser_name == 'chrome':
            potential_chrome_windows.append(window)
        elif browser_name == 'safari':
            potential_safari_windows.append(window)
        elif browser_name == 'tor':
            potential_tor_windows.append(window)
        elif browser_name == 'opera':
            potential_opera_windows.append(window)
        else:
            continue

    print("Firefox:", len(potential_firefox_windows))
    print("Chrome:", len(potential_chrome_windows))
    print("Safari:", len(potential_safari_windows))
    print("Tor:", len(potential_tor_windows))
    print("Opera:", len(potential_opera_windows))

    if len(potential_firefox_windows) >= 3:
        browsers.firefox_running()
        found['firefox'] = True
        found_firefox = True
        print("Found Firefox.")
    if len(potential_chrome_windows) >= 3:
        browsers.chrome_running()
        found['chrome'] = True
        found_chrome = True
    if len(potential_safari_windows) >= 3:
        browsers.safari_running()
        found['safari'] = True
        found_safari = True
        print("Found Safari.")
    if len(potential_tor_windows) >= 3:
        browsers.tor_running()
        found['tor'] = True
        found_tor = True
    if len(potential_opera_windows) >= 4:
        browsers.opera_running()
        found['opera'] = True
        found_opera = True
       

    if not found_tor:
        browsers.tor_off()
        found['tor'] = False
    if not found_chrome:
        browsers.chrome_off()
        found['chrome'] = False
    if not found_safari:
        browsers.safari_off()
        found['safari'] = False
    if not found_firefox:
        browsers.firefox_off()
        found['firefox'] = False
    if not found_opera:
        browsers.opera_off()
        found['opera'] = False

    return browsers, found

# The following function checks the processes on windows machines. It
# relies on the 'TOR_BROWSER_TOR_DATA_DIR environment variable in the 
# 'environ' part of the process dictionary. 
def windows_process_check(browsers, variables, found):
    firefox = variables['firefox']
    tor = variables['tor']
    chrome = variables['chrome']
    safari = variables['safari']
    opera = variables['opera']
    edge = variables['edge']

    found_firefox = False
    found_tor = False
    found_chrome = False
    found_safari = False
    found_opera = False
    found_edge = False

    for proc in psutil.process_iter():
        try:
            proc = proc.as_dict()

            if (firefox['name'] in proc['name']
                and tor['environ'] not in str(proc['environ'])
                and firefox['cmdline'] not in str(proc['cmdline'])
                and not found_firefox):
                browsers.firefox_running()
                found['firefox'] = True
                found_firefox = True

            elif (chrome['name'] in proc['name']
                and chrome['cmdline'] not in str(proc['cmdline'])
                and not found_chrome):
                browsers.chrome_running()
                found['chrome'] = True
                found_chrome = True

            elif (safari['name'] in proc['name']
                and not found_safari):
                browsers.safari_running()
                found['safari'] = True
                found_safari = True

            elif (tor['name'] in proc['name']
                and tor['environ'] in str(proc['environ'])
                and not found_tor):
                browsers.tor_running()
                found['tor'] = True
                found_tor = True

            elif (opera['name'] in proc['name']
                and 'crash' not in proc['name']
                and opera['cmdline'] not in str(proc['cmdline'])
                and not found_opera):
                browsers.opera_running()
                found_opera = True
                found['opera'] = True
        
            elif (edge['name'] in proc['name']
                and edge['cmdline'] not in str(proc['cmdline'])
                and not found_edge):
                browsers.edge_running()
                found_edge = True
                found['edge'] = True
        except psutil.NoSuchProcess as e:
            continue

    if not found_tor:
        found['tor'] = False
        browsers.tor_off()
    if not found_chrome:
        found['chrome'] = False
        browsers.chrome_off()
    if not found_safari:
        found['safari'] = False
        browsers.safari_off()
    if not found_firefox:
        found['firefox'] = False
        browsers.firefox_off()
    if not found_opera:
        found['opera'] = False
        browsers.opera_off()
    if not found_edge:
        found['edge'] = False
        browsers.edge_off()

    return browsers, found

"""The following functions deals with interacting with the 
configuration file, which stores the participant's identifier, 
the necessary variables for the platform, and the server url. """

# This function gets the configuration file for unix-like systems. If
# it doesn't exist, the file is created.
def get_ul_config():
    home = str(os.path.expanduser('~'))
    config_location = home + '/.tor_measure/config'
    if not os.path.exists(config_location):
        return generate_config(config_location)
    return read_config(config_location)

# This function gets the configuration file for windows systems. If it
# doesn't exist, the file is created.
def get_win_config():
    config_location = str("%s\\tor_measure\\config.cfg" 
                        % os.environ['APPDATA'])
    if not os.path.exists(config_location):
        return generate_config(config_location)
    return read_config(config_location)

# This function reads a configuration file and grabs the necessary data
# out of it. That data is returned in a tuple.
def read_config(config_file):
    config_parser = configparser.ConfigParser()
    config_parser.read(config_file)
    variables = config_parser.get("PLATFORM", "variables", None)
    switched_url = config.get_parser.get("SERVER", 
                "url_switched", 
                "https://iu.co1.qualtrics.com/jfe/form/SV_1zUUNkFOq0Hbmux")
    tor_url = config.get_parser.get("SERVER",
                "url_tor",
                "https://iu.co1.qualtrics.com/jfe/form/SV_1MlX8ndQNIHKgyp")
    non_tor_url = config.get_parser.get("SERVER",
                "url_non_tor",
                "https://iu.co1.qualtrics.com/jfe/form/SV_1He1PMKCwwIXC0l")
    return (variables, switched_url, tor_url, non_tor_url) 

# This function generates a configuration file when it doesn't exist.
# It generates a unique identifier and stores the server url and
# platform variables.
def generate_config(config_location):
    assert(not os.path.exists(config_location))
    config_parser = configparser.ConfigParser()
    config_parser.add_section("SERVER")
    config_parser.add_section("PLATFORM")
    switched_url = "https://iu.co1.qualtrics.com/jfe/form/SV_1zUUNkFOq0Hbmux"
    tor_url = "https://iu.co1.qualtrics.com/jfe/form/SV_1MlX8ndQNIHKgyp"
    non_tor_url = "https://iu.co1.qualtrics.com/jfe/form/SV_1He1PMKCwwIXC0l"
    config_parser.set("SERVER", "url_switched", switched_url)
    config_parser.set("SERVER", "url_tor", tor_url)
    config_parser.set("SERVER", "url_non_tor", non_tor_url)
    variables = {}

    if platform == "linux":
        variables['firefox'] = {'name':'firefox'}
        variables['tor'] = {'name':'firefox', 'cmdline':'Tor Browser'}
        variables['chrome'] = {'name':'chrome', 'cmdline':'--type'}
        variables['chromium'] = {'name':'chromium', 'cmdline':'--type'}
        variables['safari'] = {'name':'Safari', 'cmdline':'Safari.app'}
        variables['opera'] = {'name':'opera', 'cmdline':'--type'}

    elif platform == "darwin":
        variables['safari'] = {'name':'Safari', 'cmdline':'Safari.app'}
        variables['firefox'] = {'name':'firefox'}
        variables['chrome'] = {'name':'Chrome', 'cmdline':'--type'}
        variables['tor'] = {'name':'firefox', 'cmdline':'TorBrowser'}
        variables['opera'] = {'name':'Opera', 'cmdline':'--type'}

    elif platform == "win32":
        variables['firefox'] = {'name':'firefox',
                'cmdline':'-contentproc'}
        variables['tor'] = {'name':'firefox', 
                'environ':'TOR_BROWSER_TOR_DATA_DIR'}
        variables['chrome'] = {'name':'chrome', 'cmdline':'--type'}
        variables['safari'] = {'name':'safari', 'cmdline':'Safari.app'}
        variables['opera'] = {'name':'opera', 'cmdline':'--type'}
        variables['edge'] = {'name':'Edge', 'cmdline':'microsoftedgecp'}# TODO: Fill me

    else:
        raise Exception("System not supported!")

    return (variables, switched_url, tor_url, non_tor_url) 

def ul_display_survey(browsers, which, tor_url, 
                    switched_url, non_tor_url):
    opener = "open" if platform == "darwin" else "xdg-open"
    if which == browsers.TOR:
        res = subprocess.call([opener, tor_url])
    elif which == browsers.SWITCHED:
        res = subprocess.call([opener, switched_url])
    elif which == browsers.NONTOR:
        res = subprocess.call([opener, non_tor_url]) 
    else:
        raise Exception("NO IDEA HOW WE GOT HERE")

    if res != 0:
        print(res)
        raise Exception("BROWSER COULDN'T OPEN")
    LASTSURVEY = time.time()
    browsers.reset()
    time.sleep(SLEEPTIME)

def win_display_survey(browsers, which, tor_url,
                    switched_url, non_tor_url):
    if which == browsers.TOR:
        res = webbrowser.open(tor_url, new=2)
    elif which == browsers.SWITCHED:
        res = webbrowser.open(switched_url, new=2)
    elif which == browsers.NONTOR:
        res = webbrowser.open(non_tor_url, new=2) 
    else:
        raise Exception("NO IDEA HOW WE GOT HERE")

    if not res:
        raise Exception("Couldn't open web browser!")
    LASTSURVEY = time.time()
    browsers.reset()
    time.sleep(SLEEPTIME)

if platform == "linux" or platform == "darwin":
    process_check = ul_process_check
    variables, switched_url, tor_url, non_tor_url = get_ul_config()
    display_survey = ul_display_survey
if platform == "darwin":
    process_check = mac_process_check
    import Quartz
elif platform == "win32":
    process_check = windows_process_check
    variables, switched_url, tor_url, non_tor_url = get_win_config()
    display_survey = win_display_survey

if platform == 'linux' or platform == 'darwin':
    #import daemon
    import subprocess
    #install_file = open('/usr/local/tor_monitor/installed','r')
    #uid = int(install_file.readline().strip('\n'))
    #working_dir = install_file.readline().strip('\n')
    #stdout = open(working_dir + 'output', 'w+')
    #stderr = open(working_dir + 'errors', 'w+')
    #pidfile = open(working_dir + '.lock_file')
    #context = daemon.DaemonContext(#pidfile=pidfile,
    #                                working_directory=working_dir,
    #                                uid=uid,
    #                                stdout=stdout,
    #                                stderr=stderr)
    #with context:
    main()
elif platform == 'win32':
    import webbrowser
    main() 

# Library to access freebox by API
# Tested on Freebox delta
# Author : ph.larduinat at wanadoo dot fr

# Requires Python3 and requests library

import os, json, yaml, hashlib, hmac, time
import requests



class FreeFailure(Exception):
    pass



class Freebox:
    """Class to handle Freebox communication"""


    def __init__(self, freebox_url, ca=None):
        """Setup the class and check that the freebox is reachable by getting api version information"""

        self.url = freebox_url
        self.ca = ca
        self.session_token = None
        data = self._rest("/api_version")
        for k,v in data.items():
            setattr(self, k, v)


    def _rest(self, path, method="GET", parameters=None, raiseError=True):
        """All purposes http request handling, allow for standardized error handling of any request"""

        if not path.startswith("/"): path = self.api_base_url + path
        if self.session_token : header = { "X-Fbx-App-Auth" : self.session_token }
        else: header = None
        r = requests.request(method=method, url=self.url + path, headers=header, json=parameters, verify=self.ca)
        if r.status_code != 200 and raiseError:
            raise FreeFailure("Box API Error : %s [%s] %s" % (path, r.status_code, r.text))
        r = r.json()
        if "success" in r:
            if not r["success"]:
                raise FreeFailure("Box API failure : %s : %s / %s" % (path, r["error_code"], r["msg"]))
        return r["result"] if "result" in r else r


    def _auth_app(self, authFile):
        """Get app credentials from local file, request them if absent and create the credential file"""

        if os.path.exists(authFile):
            with open(authFile, "r") as f: self._auth_app_data = json.loads(f.read())
        elif not self._auth_app_data["app_id"]:
            raise FreeFailure("No application ID found")
        else:
            data = self._rest( "v4/login/authorize/", method="POST", parameters=self._auth_app_data)
            self._auth_app_data["app_token"] = data["app_token"]
            self._auth_app_data["track_id"] = data["track_id"]
            with open(authFile, "w") as f: f.write(json.dumps(self._auth_app_data))


    def connect(self, authFile, app_id=None, app_name=None, app_version=None, dev_name=None):
        """Authenticate the session, compute the session token that will be used for subsequent calls"""

        # Load/create app credentials
        self._auth_app_data = { "app_id" : app_id,
                                "app_name" : app_name,
                                "app_version" : app_version,
                                "device_name" : dev_name }
        self._auth_app(authFile)
        # Wait for access granted
        # Warning will loop until access is granted or rejected or timedout
        while True:
            r = self._rest("v4/login/authorize/%s" % self._auth_app_data["track_id"])
            if r["status"] == "granted" :
                break
            elif r["status"] == "timeout" :
                raise FreeFailure("Timeout waiting for application credentials validation")
            elif r["status"] == "denied" :
                raise FreeFailure("Application credentials request was rejected")
            time.sleep(1)

        # Get the challenge for authentication
        r = self._rest("v4/login")
        
        # Compute the response
        hexDigest = hmac.new(self._auth_app_data["app_token"].encode("utf-8"), # KEY
                             r["challenge"].encode("utf-8"),hashlib.sha1).hexdigest()

        # Get the session auth token
        params = { "app_id" : self._auth_app_data["app_id"],
                   "password" : hexDigest }
        r = self._rest("v4/login/session", method="POST", parameters=params)
        self.session_token = r["session_token"]
        self.challenge = r["challenge"]
        self.perms = r["permissions"]


    def disconnect(self):
        """Terminate the session"""

        if self.session_token:
            try:
                r = self._rest("v4/login/logout/", method="POST")
            except: # Worst case, the session will be lost whatever happen
                pass
            self.session_token = None


    def _log_change( expected, found, title, logFile):
        with open( logFile, "a") as f:
            print("Title", file=f)
            for k,v in expected.items():
                if k not in found:
                    print("\tCurrently missing key %s : %s" % (k,v), file=f)
                elif v != found[k]:
                    print("\tConfig for %s, expected : %s, found : %s" % (k, v, found[k]), file=f)
            for k,v in found.items():
                if k not in expected:
                    print("\tExceeding key %s : %s" % (k,v), file=f)


    def _get_dhcp(self, static=True):
        """get dhcp lease, static or dynamic depending on static flag"""

        dhcp = {}
        url = "v4/dhcp/static_lease/" if static else "v4/dhcp/dynamic_lease/"
        for d in self._rest(url):
            dhcp[d["hostname"]] = { "mac" : d["mac"], "ip" : d["ip"] }
        return dhcp


    def get_static_dhcp(self):
        return self._get_dhcp()


    def dhcp_to_yaml(self, dhcpFile):
        """Dump dhcp static lease to a yaml file in a format that can be reloaded"""

        dhcp = self.get_static_dhcp()
        with open(dhcpFile, "w") as f:
            f.write(yaml.dump(dhcp, default_flow_style=False))


    def get_dynamic_dhcp(self):
        return self._get_dhcp(static=False)


    def yaml_to_static_dhcp(self, dhcpFile, logFile=None):
        """Load static dhcp lease from a yaml file and add the ones that are missing"""

        curDhcp = self.get_static_dhcp()
        with open(dhcpFile, "r" ) as f:
            dhcp = yaml.load(f.read())
        if curDhcp != dhcp and logFile:
            self._log_change( dhcp, curDhcp, "Static DHCP", logFile)
        for k,v in dhcp.items():
            if k not in curDhcp:
                r = self._rest("v4/dhcp/static_lease", method="POST", parameters=v)
                print("Defined static DHCP for %" % k)
            else:
                print("Static DHCP for %s already existing")
        return curDhcp != dhcp


    def get_nat_ports(self):
        """Get defined wan port redirection"""

        redirs = {}
        ports = self._rest("v4/fw/redir/")
        for p in ports:
            dst = {}
            for i in ("hostname", "enabled", "comment", "lan_port", "wan_port_start", "wan_port_end",
                      "lan_ip", "ip_proto", "src_ip"):
                if i in p : dst[i] = p[i]
            redirs["%s/%s" %(p["wan_port_start"], p["ip_proto"])] = dst.copy()
        return redirs


    def nat_ports_to_yaml(self, portsFile):
        """Dump nat wan port redirection in a file that can be reloaded"""

        ports = self.get_nat_ports()
        with open(portsFile, "w") as f:
            f.write(yaml.dump(ports, default_flow_style=False))


    def yaml_to_nat_ports(self, portsFile, logFile=None):
        """Load nat wan port redirection and add the ones that are missing
           Key is a concatenation of <wan port>/<proto> such as "22/tcp" for ssh for example"""

        curPorts = self.get_nat_ports()
        with open(portsFile, "r") as f:
            ports = yaml.load(f.read())
        if curPorts != ports and logFile:
            self._log_change( ports, curPorts, "NAT Ports forwarding", logFile)
        for k,v in ports.items():
            if k not in curPorts:
                r = self._rest("v4/fw/redir/", method="POST", parameters=v)
                print("Defined port redirection for %s" % comment)
            else:
                print("Redirection for %s[%s] already existing" % (k, comment))
        return curPorts != ports


    def get_network_nodes(self, guest=False):
        """Enumerate hosts that have been seen by the freebox and provide IP for the host if it is reachable"""

        ##FIXME## Warning hard-coded values, don't know if it may change (but suspect that response is YES)
        zone = "wifiguest" if guest else "pub"
        hosts = {}
        for h in self._rest("v4/lan/browser/%s/" % zone):
            dst = {}
            for i in ("reachable", "last_time_reachable", "active", "persistent"):
                if i in h : dst[i] = h[i]
            if "l3connectivities" in h:
                # Look for the last reachable IPv4
                ip = [ (i["addr"],i["last_time_reachable"]) for i in h["l3connectivities"] if i["reachable"] and i["af"] == "ipv4"]
                last_ipv4 = max(ip, key=lambda item:item[1])[0] if ip else None
                if last_ipv4 : dst["ip"] = last_ipv4
            hosts[h["primary_name"]] = dst.copy()
        return hosts


    def get_connexion_info(self):
        """Get some connexion information including external IP and state"""

        return self._rest("v4/connection/")


    def get_system_info(self):
        """Get some general system information including uptime"""

        return self._rest("v4/system/")


    def reboot(self, wait=True):
        """Reboot the freebox, return when the freebox is available or False if unavailable"""
        self._rest("v4/system/reboot/")
        if not wait: return True
        maxDelay = 60
        while maxDelay > 0:
            time.sleep(5)
            try:
                self._rest("/api_version")
                break
            except:
                maxDelay -= 5
        else:
            return False
        return True


    def get_incoming_ports(self):
        """Get setting for freebox backed services"""

        incomPorts = {}
        r = self._rest("v4/fw/incoming/")
        for p in r:
            i = p["id"]
            for k in ("id", "max_port", "min_port") : del p[k]
            incomPorts[i] = p.copy()
        return incomPorts


    def incoming_ports_to_yaml(self, incomingFile):
        """Dump incoming ports in a file that can be reloaded"""

        ports = self.get_incoming_ports()
        with open(incomingFile, "w") as f:
            f.write(yaml.dump(ports, default_flow_style=False))


    def yaml_to_incoming_ports(self, incomingFile, logFile=None):
        """Load incoming ports setup from yaml file
           Currently, only enabled, in_port and protocol fields are updated"""


        with open(incomingFile, "r") as f:
            ports = yaml.load(f.read())
            curPorts = self.get_incoming_ports()
            if curPorts != ports and logFile:
                self._log_change( ports, curPorts, "Incoming ports setup", logFile)
            for p,v in ports.items():
                params = { "in_port": v["in_port"],
                           "enabled": v["enabled"],
                           "type": v["type"] }
                if v["readonly"]: del params["in_port"]
                self._rest("v4/fw/incoming/%s" % p, method="PUT", parameters=params)
            return ports != curPorts

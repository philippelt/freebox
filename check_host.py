#!/usr/bin/env python3.4


# check_host.py
#  - Without parameter, list all reachable nodes on the local lan along with their IP
#  - With a hostname as parameter, return the associated IPv4. Return status is 0 if host found else 1


import sys

from lfreebox import Freebox, FreeFailure
import setup


def main():

    try:
        target = sys.argv[1]
    except:
        target = None
    
    freebox = Freebox( setup.FREEBOX_URL, ca=setup.CACERT )
    freebox.connect( setup.AUTH_FILE )

    hosts = freebox.get_network_nodes()
    freebox.disconnect()

    if target : # Search IP for a given host
        if target in hosts and hosts[target]["reachable"]:
            print(hosts[target]["ip"])
            return 0
        else:
            return 1
    else: # List all hosts found and available on network
        for h,v in hosts.items():
            if v["reachable"] :
                print("%-20s : %s" % (h, v["ip"] if "ip" in v else "<None>"))

    return 0


if __name__ == '__main__':
    sys.exit(main())


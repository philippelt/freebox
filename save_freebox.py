#!/usr/bin/env python3.4


import sys

from lfreebox import Freebox, FreeFailure
import setup


def main():

    freebox = Freebox( setup.FREEBOX_URL, ca=setup.CACERT)
    # Connect (and create auth file if first run)
    # Don't forget to accept request on front of the box
    freebox.connect( setup.AUTH_FILE, setup.APP_ID, setup.APP_NAME, setup.APP_VERSION, setup.DEV_NAME)

    # Save static DHCP
    freebox.dhcp_to_yaml( setup.DHCP_STATIC_FILE )

    # Save nat port redirections
    freebox.nat_ports_to_yaml( setup.NAT_PORT_FILE )

    # Save local services ports
    freebox.incoming_ports_to_yaml( setup.INCOMING_PORT_FILE )

    freebox.disconnect()

    return 0


if __name__ == '__main__':
    sys.exit(main())


#!/usr/bin/env python3.4


# No error catching, in case of error, stacktrace will allow for analysis and
# Non zero return status will allow for automatic detection of problem in cron job for example


import os, sys

from lfreebox import Freebox, FreeFailure
import setup


class EndApp(Exception):
    """Execution failure (managed exception)"""
    pass


def main():

    try:
        freebox = Freebox( setup.FREEBOX_URL, ca=setup.CACERT)
        freebox.connect( setup.AUTH_FILE, setup.APP_ID, setup.APP_NAME, setup.APP_VERSION, setup.DEV_NAME)

        ports = freebox.get_nat_ports()
        if setup.TEST_SSH not in ports :
            if os.path.exists( setup.NAT_PORT_FILE ):
                freebox.yaml_to_nat_ports( setup.NAT_PORT_FILE )
            else:
                raise EndApp("No NAT port redirection file to reload")

        dhcp = freebox.get_static_dhcp()
        if setup.TEST_DHCP not in dhcp:
            if os.path.exists( setup.NAT_PORT_FILE ):
                freebox.yaml_to_static_dhcp( setup.DHCP_STATIC_FILE )
            else:
                raise EndApp("No DHCP static lease file to reload")

    except EndApp as e:
        print(e)
        return 1

    except FreeFailure as e:
        raise
        
    finally:
        freebox.disconnect()

    return 0


if __name__ == '__main__':
    sys.exit(main())


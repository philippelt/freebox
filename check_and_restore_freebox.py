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


    changed = []

    try:
        freebox = Freebox( setup.FREEBOX_URL, ca=setup.CACERT)
        freebox.connect( setup.AUTH_FILE, setup.APP_ID, setup.APP_NAME, setup.APP_VERSION, setup.DEV_NAME)

        ports = freebox.get_nat_ports()
        if setup.TEST_SSH not in ports :
            if os.path.exists( setup.NAT_PORT_FILE ):
                if freebox.yaml_to_nat_ports( setup.NAT_PORT_FILE, setup.LOG_TRACE ): changed.append("Nat_ports")
            else:
                raise EndApp("No NAT port redirection file to reload")

        dhcp = freebox.get_static_dhcp()
        if setup.TEST_DHCP not in dhcp:
            if os.path.exists( setup.NAT_PORT_FILE ):
                if freebox.yaml_to_static_dhcp( setup.DHCP_STATIC_FILE, setup.LOG_TRACE ): changed.append("Static_DHCP")
            else:
                raise EndApp("No DHCP static lease file to reload")

        # Systematically restore incoming port setup for security reasons
        incoming = freebox.get_incoming_ports()
        if os.path.exists( setup.INCOMING_PORT_FILE ):
            if freebox.yaml_to_incoming_ports( setup.INCOMING_PORT_FILE, setup.LOG_TRACE ) : changed.append("Incoming_ports")
        else:
            raise EndApp("No incoming port setup file to reload")

        # Notify if differences are found between expected setup and actual setup
        if changed :
            print("Some items has changed : ", ",".join(changed))
            return 1

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


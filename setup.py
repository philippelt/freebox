# Parameters setup

# Freebox access, to allow for https, use free defined fqdn
# ** IMPORTANT **
# Hardcode fqdn to local address to access from lan in /etc/hosts of the querying system
# This will allow your API to access your box using regular 443 port even if remote access is not allowed
# In /etc/hosts (with x.y being the local IP address of your box):
# 192.168.x.y  <your generated name>.fbxos.fr
FREEBOX = "<your generated name>.fbxos.fr"
FREEBOX_URL = "https://%s" % FREEBOX

# Free CA data (concatenation of 2 CA PEM certs files available on https://dev.freebox.fr/sdk/os/)
CACERT = "/path/to/ca/file"

# Application credentials, will save application token on first invocation
# Note: grant must be provided through physical box validation (OK button in the front)
# You can almost put what you want in these fields
APP_ID = "<your app id>"
APP_NAME = "<your app name>"
APP_VERSION = "0.0.1"
DEV_NAME = "<Accessing device>"

# Local files to save application credentials
AUTH_FILE = "/path/to/cred/file"

# Local files to save critical configuration elements
NAT_PORT_FILE = "/path/to/ports/yaml"
INCOMING_PORT_FILE = "/path/to/incoming/yaml"
DHCP_STATIC_FILE = "/path/to/dhcp/yaml"

# Port redirection to check to decide if reload is required (preserved or all losts)
TEST_SSH = "22/tcp" # Just an exemple, it is usually a bad idea to expose port 22 on internet

# Static DHCP lease to check to decide if reload is required
TEST_DHCP = "mynas"

# Log file to keep track of changes identified during checkup
LOG_TRACE = "/var/log/restore_freebox.log"

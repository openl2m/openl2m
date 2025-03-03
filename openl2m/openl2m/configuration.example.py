#########################
#                       #
#   Required settings   #
#                       #
#########################

# This is a list of valid fully-qualified domain names (FQDNs) for the OpenL2M server. OpenL2M will not permit write
# access to the server via any other hostnames. The first FQDN in the list will be treated as the preferred name.
#
# Example: ALLOWED_HOSTS = ['openl2m.example.com', 'openl2m.internal.local']
ALLOWED_HOSTS = ['*']

# The FQDN with scheme for your domain, to protect against Cross Site Request Forgery:
# you need to include 'https://' or 'http://' if no secured!
# you can include IP address if needed...
CSRF_TRUSTED_ORIGINS = ['https://openl2m.example.net', 'https://10.0.0.1']

# This key is used for secure generation of random numbers and strings. It must never be exposed outside of this file.
# For optimal security, SECRET_KEY should be at least 50 characters in length and contain a mix of letters, numbers, and
# symbols. OpenL2M will not run without this defined. For more information, see
# https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-SECRET_KEY
# SECURITY WARNING: keep the secret key used in production secret!
# you can generate a key with the "openl2m/generate_secret_key.py" script.
SECRET_KEY = ''

# PostgreSQL database configuration.
DATABASE = {
    'NAME': 'openl2m',  # Database name
    'USER': 'openl2m',  # PostgreSQL username
    'PASSWORD': 'xxxxxxxxxxx',  # PostgreSQL password
    'HOST': 'localhost',  # Database server
    'PORT': '',  # Database port (leave blank for default)
}

#########################
#                       #
#   Optional settings   #
#                       #
#########################
# OpenL2M "administrator" emails. This is a list of all the people who get
# code error notifications, and other emails (see below)
# This is not related to users with superuser access.
ADMINS = [
    # ('John', 'john@example.com'),
    # ('Mary', 'mary@example.com')
]

# Optionally display a persistent banner at the top and/or bottom of every page. HTML is allowed. To display the same
# content in both banners, define BANNER_TOP and set BANNER_BOTTOM = BANNER_TOP.
BANNER_TOP = 'Top Banner Information Line'
BANNER_BOTTOM = 'Bottom Banner Line'

# Text to include on the login page above the login form. HTML is allowed.
BANNER_LOGIN = 'Login Banner'

# Base URL path if accessing OpenL2M within a directory. For example, if installed at http://example.com/openl2m/, set:
# BASE_PATH = 'openl2m/'
BASE_PATH = ''

# Keep activity log entries for this many day. 0 disables (keep forever)
LOG_MAX_AGE = 180

# the maximum number of recent switch activity log entries shown when accessing a switch
# Note that only change & error logs are shown, not 'view' log entries
RECENT_SWITCH_LOG_COUNT = 25

# API Cross-Origin Resource Sharing (CORS) settings. If CORS_ORIGIN_ALLOW_ALL is set to True, all origins will be
# allowed. Otherwise, define a list of allowed origins using either CORS_ORIGIN_WHITELIST or
# CORS_ORIGIN_REGEX_WHITELIST. For more information, see https://github.com/ottoyiu/django-cors-headers
CORS_ORIGIN_ALLOW_ALL = False
CORS_ORIGIN_WHITELIST = [
    # 'hostname.example.com',
]
CORS_ORIGIN_REGEX_WHITELIST = [
    # r'^(https?://)?(\w+\.)?example\.com$',
]

# The length of time (in seconds) for which a user will remain logged into the web UI before being prompted to
# re-authenticate. (Default: 1800 [30 minutes]) See also LOGOUT_ON_INACTIVITY
LOGIN_TIMEOUT = 1800

# if this is set, then the login timeout is treated as inactivity timeout.
# if False, default Django behaviour is LOGIN_TIMEOUT is max time session will last.
LOGOUT_ON_INACTIVITY = True

# Setting this to True will display a "maintenance mode" banner at the top of every page.
MAINTENANCE_MODE = False

# Determine how many objects to display per page within a list. (Default: 50)
PAGINATE_COUNT = 50

# When determining the primary IP address for a device, IPv6 is preferred over IPv4 by default. Set this to True to
# prefer IPv4 instead.
PREFER_IPV4 = True  # IPv6 has not been tested!

# By default, OpenL2M will store session data in the database. Alternatively, a file path can be specified here to use
# local file storage instead. (This can be useful for enabling authentication on a standby instance with read-only
# database access.) Note that the user as which OpenL2M runs must have read and write permissions to this path.
SESSION_FILE_PATH = None

# if using SSL, these should be set to True:
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# override the maximum GET/POST item count.
# with large numbers of switches in a group, we may exceed the default (1000):
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

# Time zone (default: UTC)
TIME_ZONE = 'UTC'

# Date/time formatting. See the following link for supported formats:
# https://docs.djangoproject.com/en/dev/ref/templates/builtins/#date
DATE_FORMAT = 'N j, Y'
SHORT_DATE_FORMAT = 'Y-m-d'
TIME_FORMAT = 'g:i a'
SHORT_TIME_FORMAT = 'H:i:s'
DATETIME_FORMAT = 'N j, Y g:i a'
SHORT_DATETIME_FORMAT = 'Y-m-d H:i'

# Delay in seconds when we disable and re-enable an interface, or PoE
PORT_TOGGLE_DELAY = 5

# PoE toggling, disable PoE, wait this long, and enable property
POE_TOGGLE_DELAY = 5

# If enabled, allow PoE enable/disable for all users with access to switch,
# regardless of other access to the interface
ALWAYS_ALLOW_POE_TOGGLE = False

# If True, all non-ethernet interfaces are hidden from all users, including admins
HIDE_NONE_ETHERNET_INTERFACES = False

# Customizable URLs for Switch, Interface, Ethernet and IP addresses
#
# Each is a list of dictionary items. Each dictionary item have have the following keys:
#
# 'url':  the mandatory url for the link
#
# 'hint': the optional url hint (ie hover-over text)
#
# 'target' is optional. Any value that evaluates to "True" will cause 'target="_blank"' to be added
#  to the link, to open in new window or tab (per browser settings).
#
# 'icon': a path or url to the image for the link
#
# 'alt': alternative text if icon is used.
#
# fa_icon': the name of the FontAwesome 5 icon to use; this overrides the "icon" field above.
# Refer to Font Awesome v5 icon collection by name,
# see https://fontawesome.com/icons?d=gallery&m=free
#
# You can use the following template strings in the url field:
# {{ switch.name }} - name as configured by admin switch object
# {{ switch.hostname }} - hostname as set on device (read via snmp, ssh, etc.)
# {{ switch.primary_ip4 }}
# {{ switch.nms_id }}
# 'url' is mandatory.
#

#
# SWITCH_INFO_URLS is a list of dictionaries with one or more links to put in front of the device name.
#

# uncomment this as needed:
# SWITCH_INFO_URLS = [
#     # This example is for Akips, and provides a direct link to the switch page in Akips:
#     {
#         'url': 'https://akips.yoursite.com/dashboard?mode=device;device_list={{ switch.hostname }};',
#         'hint': 'Click here to see AKIPS data for this switch',
#         'target': True,
#         'icon': '/static/img/nms.png',
#         # or use the icon from Akip:
#         # 'icon': 'https://akips.yoursite/img/favicon-32.png',
#         'alt': 'Akips NMS Icon',
#         # or use any Font Awesome 5 icon:
#         # 'fa_icon': 'fa-chart-area',
#     },
#     # this would be a link to a LibreNMS or Observium page.
#     # Note you have to fill in the "nms_id" field for each switch for this to work!
#     {
#         'url': 'https://librenms.yoursite.com/device/device={{ switch.nms_id }}/',
#         'hint': 'Click here to see LibreNMS data for this switch',
#         'target': True,
#         'icon': '/static/img/nms.png',
#         # or use the icon from LibreNMS:
#         # 'icon': 'http://librenms.yoursite.com/images/favicon-16x16.png',
#         # or
#         # 'icon': 'http://librenms.yoursite.com/images/favicon-32x32.png',
#         # 'icon': 'http://librenms.yoursite.com/images/favicon.ico',
#         'alt': 'LibreNMS Icon',
#         # or use any Font Awesome 5 icon:
#         # 'fa_icon': 'fa-chart-area',
#     },
# ]

#
# SWITCH_INFO_URLS_STAFF is identical to SWITCH_INFO_URLS, but only shows for Staff of SuperUsers (admins)
# See explanation above.
#

# uncomment this as needed:
# SWITCH_INFO_URLS_STAFF = [
#     # This example is for SSH. Note this require browsers to handle "ssh://" !
#     {
#         'url': 'ssh://{{ switch.primary_ip4 }}/',
#         'hint': 'Click here to SSH to this switch',
#         'target': True,
#         # 'icon': '/static/img/nms.png',
#         # or use the icon from a URL:
#         # 'icon': 'https://some.site.com/favicon.png',
#         'alt': 'SSH Icon',
#         # or use any Font Awesome 5 icon:
#         'fa_icon': 'fa-desktop',
#     },
#     # this would be a link to a another management tool for admins.
#     {
#         'url': 'https://yourtool.yoursite.com/device/device={{ switch.hostname }}/',
#         'hint': 'Click here to go to some tool!',
#         'target': True,
#         'icon': '/static/img/nms.png',
#         'alt': 'Tool Icon',
#         # or use any Font Awesome 5 icon:
#         # 'fa_icon': 'fa-chart-area',
#     },
# ]

#
# SWITCH_INFO_URLS_ADMINS is identical to SWITCH_INFO_URLS, but only shows for SuperUsers (admins)
# See explanation above.
#

# uncomment this as needed:
# SWITCH_INFO_URLS_ADMINS = [
#     # This example is for SSH. Note this require browsers to handle "ssh://" !
#     {
#         'url': 'ssh://{{ switch.primary_ip4 }}/',
#         'hint': 'Click here to SSH to this switch',
#         'target': True,
#         # 'icon': '/static/img/nms.png',
#         # or use the icon from a URL:
#         # 'icon': 'https://some.site.com/favicon.png',
#         'alt': 'SSH Icon',
#         # or use any Font Awesome 5 icon:
#         'fa_icon': 'fa-desktop',
#     },
#     # this would be a link to a another management tool for admins.
#     {
#         'url': 'https://yourtool.yoursite.com/device/device={{ switch.hostname }}/',
#         'hint': 'Click here to go to some tool!',
#         'target': True,
#         'icon': '/static/img/nms.png',
#         'alt': 'Tool Icon',
#         # or use any Font Awesome 5 icon:
#         # 'fa_icon': 'fa-chart-area',
#     },
# ]

#
# INTERFACE_INFO_URLS is a list of dictionaries with one or more links to put in front of interfaces.
#
# You can use all the {{ switch }} templates above, as well as
# {{ iface.name }}
# {{ iface.index }} - the SNMP interface index ifIndex
# {{ iface.description }} - the interface description, for SNMP interface ifAlias, probably not useful.
#

# uncomment this as needed:
# INTERFACE_INFO_URLS = [
#     {
#         'name': 'Akips',
#         'url': 'https://akips.yoursite.com/dashboard?mode=interface;time=last3h;controls=interface;device={{ switch.hostname }};child={{ iface.name }}',
#         'hint': 'Click here to see AKIPS data for this interface',
#         'target': True,
#         'icon': '/static/img/nms.png',
#         'alt': 'NMS Icon',
#         # or use any Font Awesome 5 icon:
#         # 'fa_icon': 'fa-chart-area',
#     },
# ]

#
# VLAN_INFO_URLS is a list of dictionaries with one or more links to put in front of vlans.
#
# You can use the following templates:
# {{ vlan.name }}   - the name :-)
# {{ vlan.id }}     - the vlan id :-)
#

# uncomment this as needed:
# VLAN_INFO_URLS = [
#     {
#         'name': 'IPAM',
#         'url': 'https://ipam.yoursite.com/something/search?vlan={{ vlan.id }}',
#         'hint': 'Click here to see IPAM data about this VLAN',
#         'target': True,
#         'icon': '/static/img/ipam.png',
#         'alt': 'NMS Icon',
#         # or use any Font Awesome 5 icon:
#         # 'fa_icon': 'fa-chart-area',
#     },
# ]

#
# IP4_INFO_URLS is a list of dictionaries that will be links shown on found IP addresses.
# The idea is that you may want to provide a link to your device registration site, as well as your logging (eg Splunk)
#
# You can use the following templates:
# {{ ip4 }} - the ip v4 address x.x.x.x
#

# uncomment this as needed:
# IP4_INFO_URLS = [
#     {
#         'name': 'IPAM',
#         'url': 'https://ipam.yoursite.com/something/search?ipv4={{ ip4 }}',
#         'hint': 'Click here to see IPAM data about this IPv4 address',
#         'target': True,
#         'icon': '/static/img/ipam.png',
#         'alt': 'NMS Icon',
#         # or use any Font Awesome 5 icon:
#         # 'fa_icon': 'fa-chart-area',
#     },
#     # another example, a direct link to an ELK stack log parser for the ipv4 addresses
#     # note this is completely fictitious!
#     {
#         'name': 'ELK Stack',
#         'url': 'https://elkstack.yoursite.com/search?ipv4={{ ip4 }}',
#         'hint': 'Click here to see ELK Stack log data about this IPv4 address',
#         'target': True,
#         'icon': '/static/img/general-info.png',
#         'alt': 'ELK Stack Icon',
#         # or use any Font Awesome 5 icon:
#         # 'fa_icon': 'fa-chart-area',
#     },
# ]

#
# ETHERNET_INFO_URLS is a list of dictionaries that will be links shown on found ethernet addresses.
# The idea is that you may want to provide a link to your device registration site, as well as your logging (eg Splunk)
#
# You can use the following templates:
# {{ ethernet }} - the formatted ethernet string
#

# uncomment this as needed:
# ETHERNET_INFO_URLS = [
#     {
#         'name': 'IPAM',
#         'url': 'https://ipam.yoursite.com/something/search?ethernet={{ ethernet }}',
#         'hint': 'Click here to see IPAM data about this ethernet address',
#         'target': True,
#         'icon': '/static/img/ipam.png',
#         'alt': 'NMS Icon',
#         # or use any Font Awesome 5 icon:
#         # 'fa_icon': 'fa-chart-area',
#     },
#     # another example, a direct link to an ELK stack log parser for the ethernet addresses
#     # note this is completely fictitious!
#     {
#         'name': 'ELK Stack',
#         'url': 'https://elkstack.yoursite.com/search?ethernet={{ ethernet }}',
#         'hint': 'Click here to see ELK Stack log data about this eithernet address',
#         'target': True,
#         'icon': '/static/img/general-info.png',
#         'alt': 'ELK Stack Icon',
#         # or use any Font Awesome 5 icon:
#         # 'fa_icon': 'fa-chart-area',
#     },
# ]


# Ethernet display format, either
# COLON = 0  e.g. 00:11:22:33:44:55
# HYPHEN = 1 e.g. 00-11-22-33-44-55
# CISCO = 2  e.g.  0011.2233.4455
ETH_FORMAT = 0

#
# various regular expression to remove interfaces from the user
# this uses the Python 're' module.
#
# IF MATCHED, INTERFACES WILL NOT BE SHOWN TO REGULAR USERS!
#

# this regex matches the interface name, GigabitEthernetx/x/x
# matched interface are hidden:
# IFACE_HIDE_REGEX_IFNAME = "^TenGig"

# this regex matches the interface 'ifAlias' aka. the interface description
# use e.g. to hide "Trunk" interfaces based on description.
# matched interface are hidden:
# IFACE_HIDE_REGEX_IFDESCR = "BLUE"

# hide interfaces with speeds above this value in Mbps.
# e.g. hide 10G and above, set to 9500. 0 disables this filter.
# matched interface are hidden:
# IFACE_HIDE_SPEED_ABOVE = 9500

#
# a settings to dis-allow new interface description formats.
# again uses Python 're' module to match.
#
# if the new description matches this reg ex, do not allow it
# matched descriptions are not allowed:
# IFACE_ALIAS_NOT_ALLOW_REGEX = "^Po|NOT ALLOWED"

#
# a setting to force a persistant part of a description.
# if the existing description start with this match,
# keep that part of the description when a user edits it.
# E.g. the below regex for port-patch descriptions of format "D.nnn" to be kept
# while allowing 'real' descriptions to be added after it
# matched descriptions are not allowed:
# IFACE_ALIAS_KEEP_BEGINNING_REGEX = "D.\d+"

# if true, routed interface IPv4 addresses will show prefixlen. Default is subnet mask.
IFACE_IP4_SHOW_PREFIXLEN = False

#
# Custom Menu items, consisting of MENU_INFO_URLS and MENU_ON_RIGHT.
#

# MENU_ON_RIGHT = True, indicates the custom menu will be on the right side of the top bar
MENU_ON_RIGHT = True

# MENU_INFO_URLS is a dictionary of dictionaries to form a menu structure of links in the top bar
# the initial dict() is the menu header name, and the containing dict() are the url links under it
#
# You can also use the Font Awesome 5 icons.
# To use add an entry 'fa_icon': 'font-awesome-icon-name'
# This will take the place of the 'icon' entry (i.e. it will not be used if fa-icon is defined!)
#

# uncomment this as needed:
# MENU_INFO_URLS['Menu 1'] = [
#     {
#         'name': 'Entry 1',
#         'url': 'http://example.com',
#         'target': True,
#         'fa_icon': 'fa-car'
#     },
#     {
#         'name': 'Entry 2',
#         'url': 'https://ssl.example.com',
#         'target': True,
#         'icon': '/static/img/ipam.png',
#         'alt': 'Cyder Icon',
#     },
# ]
# MENU_INFO_URLS['Menu 2'] = [
#     {
#         'name': 'Entry 3',
#         'url': 'http://example.com/test.php=test',
#         'target': True,
#         'icon': '/static/img/ipam.png',
#         'alt': 'Cyder Icon',
#     },
#     {
#         'name': 'Entry 4',
#         'url': 'https://ssl.example.com',
#         'target': True,
#         'fa_icon': 'fa-address-book'
#     },
# ]

# Some html colors to choose interface admin status.
# Colors used behind the interface name (ie background):
# A great place for colors: https://www.rapidtables.com/web/color/
# Admin-UP, No Link:
BGCOLOR_IF_ADMIN_UP = "#98FB98"  # darker/lighter green
# Admin-UP, Link:
BGCOLOR_IF_ADMIN_UP_UP = "#ADFF2F"  # brighter green
# Admin disabled
BGCOLOR_IF_ADMIN_DOWN = "#EB5B5B"  # red

# login view organization. Number of colums in the "matrix" groups display
# Can be no more then 6! Best if 12 is divisible this number (e.g. 2, 3, 4, or 6)
TOPMENU_MAX_COLUMNS = 4

# show the switch search form in nav bar
SWITCH_SEARCH_FORM = True

# SNMP related settings, normally not needed to change.
SNMP_TIMEOUT = 5  # in seconds
SNMP_RETRIES = 3
# this is the maximum count of MIB entities returned in a single reply in response to the get-bulk calls we make.
# note that some devices cannot handle the default 25, and you may need to lower this e.g. 10
# see the references in the documentation for more information.
SNMP_MAX_REPETITIONS = 25

# Syslog settings
# if SYSLOG_HOST is defined (default=False), log entries will also be sent here, to the 'user' facility:
# SYSLOG_HOST = 'localhost'
# if needed, you can change the UDP port:
# SYSLOG_PORT = 514
# By default SYSLOG_JSON=True, and syslog entries will be send in Json format for easier parsing.
# If not, a textual version of log event will be sent.
# SYSLOG_JSON = True

# Email settings, used to send results of commands and other emails.
# the default uses the local plain old smtp server on port 25
# see the installation docs or Django docs for other options.
EMAIL_HOST = 'localhost'
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_PORT = 25
EMAIL_TIMEOUT = 10  # in seconds
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False
EMAIL_SSL_CERTFILE = None
EMAIL_SSL_KEYFILE = None

# to receive bounced emails, make sure this is a valid return address!
EMAIL_FROM_ADDRESS = '<openl2m@localhost>'
# the subject Prefix for admin emails:
EMAIL_SUBJECT_PREFIX = '[OpenL2M-Admin] '
# the subject Prefix for regular user emails:
EMAIL_SUBJECT_PREFIX_USER = '[OpenL2M] '


# Vendor specific setings

# the max time to wait, in seconds, for a new-style "cisco-copy-mib" "write mem" to complete:
CISCO_WRITE_MEM_MAX_WAIT = 5

# SSH connect timeout, default = 5 seconds (Netmiko library default = 10)
# Only used on SSH command sessions.
SSH_CONNECT_TIMEOUT = 5

# SSH command read timeout, default = 15 (Netmiko library default = 10)
SSH_COMMAND_TIMEOUT = 15

# connect timeout for Junos devices via the Netconf interface
JUNOS_PYEZ_CONN_TIMEOUT = 10

# perform hostname lookup from IP addresses found in ARP info, Admin pages, etc.
# Note this could have impact on page rendering, depending on how fast your
# dns resolution is and how may retries the underlying host OS is configured for.

# perform hostname lookup for admin page showing connected user
LOOKUP_HOSTNAME_ADMIN = False
# for IP addresses in device ARP tables, perform hostname lookup
LOOKUP_HOSTNAME_ARP = False
# lookup hostname if LLD neighbor device has an IP address as chassis address type
LOOKUP_HOSTNAME_LLDP = False
# lookup hostnames for routed interface IP addresses.
LOOKUP_HOSTNAME_ROUTED_IP = False

# REST API Settings
#
# API access can be turn off. If False API access is disabled.
API_ENABLED = True
# if True, users can see their tokens again after they have been created.
# if False, only last few chars will be shown.
ALLOW_TOKEN_RETRIEVAL = False
# maximum number of tokens per user
MAX_API_TOKENS = 3
# If the API client IP is in this denied list, access is globally denied.
# This is a comma-separated list of IPv4/IPv6 networks in CIDR notation.
# e.g. "192.168.1.0/24, 10.1.0.0/16"
# Leave blank for no restrictions.
API_CLIENT_IP_DENIED = ""
# If the API client IP is in this allowed list, access is globally allowed.
# Each Token can further restricted by setting the 'allowed_ips' attribute.
# This is a comma-separated list of IPv4/IPv6 networks in CIDR notation,
# e.g. "192.168.0.0/16, 10.0.0.0/8, 127.0.0.1"
# Leave blank for no restrictions.
API_CLIENT_IP_ALLOWED = ""
# Max token duration, in days. If user sets token expiration beyond this number
# of days into future, it will be limited to this number of days into future.
# Ignored if 0.
API_MAX_TOKEN_DURATION = 0

# WEB-UI Data Export Settings
#
# if you want to disallow downloading of ethernet-arp-lldp information
# into Excel spreadsheets, set this to False.
ALLOW_ARP_LLDP_DOWNLOAD = True

# Show Top-N active users, devices, etc.
# if set to 0, this view is disabled! If > 0, will show in menu for all users:
TOP_ACTIVITY = 10
# number of days for the "Top N" activity:
TOP_ACTIVITY_DAYS = 7

#
# Neighbor device settings, used for LLDP Neighbor tab, and Mermaid graphical view
# Below are the defaults, adjust as needed.
#
# max neighbors for Top-Down diagram. Larger becomes Left-to-Right
# NB_MAX_FOR_TD = 5
#
# this segment maps device types to FontAwesome icon names to be used during neighbor display.
# if you change this, make sure you know the proper "Free" FA icon name
# see more at https://fontawesome.com/search?o=r&m=free
# NB_ICON_NONE = "fa-question"
# NB_ICON_WLAN = "fa-wifi"
# NB_ICON_PHONE = "fa-phone"
# NB_ICON_ROUTER = "fa-cogs"
# NB_ICON_STATION = "fa-desktop"
# NB_ICON_BRIDGE = "fa-ethernet"
# NB_ICON_REPEATER = "fa-ethernet"
# NB_ICON_OTHER = "fa-question"
#

# Mermaid graphs of connected devices  (neighbors) can be simple or expanded.
# Simple shows current device interface and connected neigbor.
# Expanded also show the remote neighbor interface, if shown.
# default is simple, ie. False. Set to True for slightly more interesting graph.
# MM_GRAPH_EXPANDED = False

# this is the Mermaid.js style for the various device types.
# this defaults to 'standard' style, but you can add fill-in colors, outlines, etc.
# see more at https://mermaid.js.org/syntax/block.html#example-styling-a-single-block
# MM_NB_STYLE_NONE = ""
# MM_NB_STYLE_WLAN = ""
# MM_NB_STYLE_PHONE = ""
# MM_NB_STYLE_ROUTER = ""
# MM_NB_STYLE_STATION = ""
# MM_NB_STYLE_BRIDGE = ""
# MM_NB_STYLE_REPEATER = ""
# MM_NB_STYLE_OTHER = ""


# this is a basic logging configuration for the Django settings.LOGGING
# this is only used in the dprint() function when DEBUG=True. This prints to the console.
# I.e. use this when in "developer mode" while running "django runserver".
# See the documentation for more logging configuration details.
# Example:
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'console': {
#             # a very minimal formats:
#             'format': '%(message)s',
#         },
#         'header': {
#             # minimal format with header:
#             'format': '[OpenL2M] %(message)s',
#         },
#     },
#     'handlers': {
#         'console': {
#             'class': 'logging.StreamHandler',
#             'formatter': 'console',
#         },
#     },
#     'loggers': {
#         'openl2m.console': {
#             'handlers': ['console'],
#             'level': 'DEBUG',
#             'formatter': 'minimal',
#         },
#     },
# }

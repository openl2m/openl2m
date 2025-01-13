#
# This file is part of Open Layer 2 Management (OpenL2M).
#
# OpenL2M is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with OpenL2M. If not, see <http://www.gnu.org/licenses/>.
#
import csv
import json

from django.conf import settings
from django import template
from django.template import Template, Context
from django.utils.html import mark_safe
from django.urls import reverse

from switches.constants import SWITCH_VIEW_BASIC, SWITCH_VIEW_DETAILS
from switches.connect.classes import Interface
from switches.connect.constants import (
    ENTITY_CLASS_NAME,
    POE_PSE_STATUS_ON,
    POE_PSE_STATUS_OFF,
    POE_PSE_STATUS_FAULT,
    IF_DUPLEX_FULL,
    IF_DUPLEX_HALF,
    LLDP_CAPABILITIES_NONE,
    LLDP_CAPABILITIES_WLAN,
    LLDP_CAPABILITIES_PHONE,
    LLDP_CAPABILITIES_ROUTER,
    LLDP_CAPABILITIES_STATION,
    LLDP_CAPABILITIES_BRIDGE,
    LLDP_CAPABILITIES_REPEATER,
    LLDP_CAPABILITIES_OTHER,
)

from switches.utils import dprint

# see https://docs.djangoproject.com/en/2.2/ref/templates/api/
# and https://docs.djangoproject.com/en/2.2/howto/custom-template-tags/

register = template.Library()


def build_url_string(values):
    """
    Build a external url string from the url values dict() given
    Used to build custom links from "settings" variables
    """
    if 'target' in values.keys() and values['target']:
        s = '<a target="_blank"'
    else:
        s = "<a"
    s = s + f" href=\"{values['url']}\""
    if 'alt' in values.keys() and values['alt']:
        s = s + f" alt=\"{values['alt']}\""
    if 'hint' in values.keys():
        s = s + f" data-bs-toggle=\"tooltip\" data-bs-title=\"{values['hint']}\""
    s = s + ">"
    if 'fa_icon' in values.keys():
        s = s + f" <i class=\"fas {values['fa_icon']}\" aria-hidden=\"false\"></i>"
    elif 'icon' in values.keys():
        s = (
            s
            + f" <img src=\"{values['icon']}\" aria-hidden=\"false\" alt=\"{values['alt']}\" height=\"24\" width=\"24\">"
        )
    s = s + "</a> "
    return s


def get_switch_link(group_id, switch_id, switch):
    """
    Build custom html link to switch, based on switch attributes
    """
    s = '<a class="list-group-item list-group-item-action" '
    if switch['default_view'] == SWITCH_VIEW_BASIC:
        s = s + f'href="{reverse("switches:switch_basics", kwargs={"group_id": group_id, "switch_id": switch_id})}"'
    else:
        s = s + f'href="{reverse("switches:switch_arp_lldp", kwargs={"group_id": group_id, "switch_id": switch_id})}"'
    if switch['description']:
        s = s + f" data-bs-toggle=\"tooltip\" data-bs-title=\"{switch['description']}\""
    # do proper indenting:
    indent = ''
    for i in range(switch['indent_level']):
        indent = indent + "&nbsp;&nbsp;&nbsp;"
    # and return full device menu item link:
    return s + f'>{indent}{switch["name"]}</a>'


def get_switch_url(group_id, switch_id, indent_level=0, view=""):
    """
    Build just the URL portion of the link to a switch
    """
    indent = ''
    for i in range(indent_level):
        indent = indent + "&nbsp;&nbsp;&nbsp;"
    if view:
        view = f"{view}/"
    return f"{indent}<a href=\"/switches/{group_id}/{switch_id}/{view}\""


@register.filter
def get_list_value_from_json(s, index):
    """
    Get the value for the given index from a JSON string representing a list.
    call as {{ list|get_list_value_from_json:index }}
    """
    if index:
        return json.loads(s)[index]


@register.filter
def get_list_value(list, index):
    """
    Get a list value for the given index.
    call as {{ list|get_list_value:index }}
    """
    if index:
        return list[index]


@register.filter
def get_dictionary_value(d, key):
    """
    Get a dictionary value for the given key.
    call as {{ dictionary|get_dictonary_value:key }}
    """
    if key:
        return d.get(key)


@register.filter
def get_dictionary_value_from_json(s, key):
    """
    Get the value for the given key from a JSON string representing a dictionary.
    call as {{ dictionary_string|get_dictonary_value_from_json:key }}
    """
    if key:
        return json.loads(s).get(key)


@register.filter
def bitwise_and(value, arg):
    """
    This is used in some templates to show the bitmat values of switch.capabilities
    """
    return bool(value & arg)


@register.filter
def get_device_class(device):
    """
    Return an html string that represent the data of the device given.
    A device is a switch, a stack, or a switch in that stack.
    """
    return ENTITY_CLASS_NAME[device.type]


@register.filter
def get_my_results(results, group_count):
    """
    Display the search results as a list of links.
    """
    num = len(results)
    if num == 0:
        return "We did not find any matching switches!"
    found = ""
    for group_id, switch_id, name, description, default_view, group_name in results:
        link = f"\n<a class=\"list-group-item list-group-item-action\" href=\"/switches/{group_id}/{switch_id}/"
        if default_view == SWITCH_VIEW_DETAILS:
            link += "details/\""
        else:
            link += "\""
        if description:
            link += f" data-bs-toggle=\"tooltip\" data-bs-title=\"{description}\""
        if group_count > 1:
            found += f"{link}>{name} ({group_name})</a>"
        else:
            found += f"{link}>{name}</a>"

    return mark_safe(found)


def get_group_menu(group, group_id, open=False):
    """Show the menu for just a single group

    Args:
        group (dict()): the group to display.
        group_id (int): the group ID.
        open (bool, optional): If True, show the group "opened up", ie. not collapsed. Defaults to False.

    Returns:
        str: the str() with the proper html for this group.
    """
    # header for collapsible items, i.e. the switchgroup name
    s = f"\n<!-- Group {group_id} -->\n<div class=\"d-grid\">\n"

    # parse open/closed options:
    if open:
        expanded = "true"
        show = "show"
    else:
        expanded = "false"
        show = ""

    # wrap description around the menu button, set full size...
    if group["description"]:
        s = s + f"\n<span class=\"d-grid\" data-bs-toggle=\"tooltip\" data-bs-title=\"{group['description']}\">"

    # add the button
    s = s + "\n"
    s = (
        s
        + f'<button class="btn btn-outline-secondary mb-2" type="button" data-bs-toggle="collapse" data-bs-target="#group{group_id}" aria-expanded="{expanded}" aria-controls="group{group_id}">'
    )
    # use display name if set, else just group name"
    if group["display_name"]:
        s = s + group["display_name"]
    else:
        s = s + group["name"]
    if group["read_only"]:
        s = s + " (r/o)"
    # end button:
    s = s + "\n</button>"

    # end description wrapper span:
    if group["description"]:
        s = s + "\n</span>"

    # end d-grip
    s = s + "\n</div>"

    # the list of devices in this menu, ie collapsible items:
    s = (
        s
        + f'<div class="collapse {show} overflow-scroll" id="group{group_id}" style="max-height: 200px;"><div class="list-group">'
    )
    for switch_id, switch in group['members'].items():
        s = s + f"\n{get_switch_link(group_id, switch_id, switch)}"
    # end devices div, list and group menu
    s = s + "\n</div>\n</div>\n<!-- END Group {group_id} -->\n\n"
    # done:
    return s


@register.filter
def get_my_group_menu(groups):
    """
    Build custom html menu of all the switchgroups and their switches
    """
    dprint('get_my_group_menu()')
    # dprint(pprint.pformat(groups))

    num_groups = len(groups)
    if not num_groups:
        s = '<div class="card border-warning"><div class="card-header bg-warning"><i class="fas fa-exclamation-triangle"></i>&nbsp;<strong>No groups assigned!</strong></div><div class="card-body row justify-content-md-center">You are not a member of any switch groups! Please contact the OpenL2M administrator.</div></div>'
        return mark_safe(s)

    # the Group Title:
    if num_groups == 1:
        # one group only:
        text = 'Group'
        open = True  # open menu dropdown
    else:
        # multiple groups:
        text = 'Groups'
        open = False  # start with all closed

    s = f'<div class="container-fluid"><div class="card border-default"><div class="card-header bg-default"><strong>My Device {text}:</strong></div>'

    # start groups wrapper
    s = s + '\n<div class="card-body">\n'  # end header row (for html human readability)

    # calculate column width, if set. Bootstrap uses 12 grid columns per page, max width we use is 2 grids
    if settings.TOPMENU_MAX_COLUMNS > 6:
        col_width = 2
        max_columns = 6
    else:
        col_width = int(12 / settings.TOPMENU_MAX_COLUMNS)
        max_columns = settings.TOPMENU_MAX_COLUMNS

    # now list the groups:
    group_num = 0
    for group_id, group in groups.items():
        group_num += 1
        if not ((group_num - 1) % max_columns):
            # end previous row, if needed
            if group_num > 1:
                s = s + "\n</div>"
            # and start a new row!
            s = s + "\n\n<div class=\"row\">"
        # add new column:
        s = s + f"\n <div class=\"col-{col_width}\">"

        # represent the group menu:
        s = s + get_group_menu(group=group, group_id=group_id, open=open)

        # and end this group column:
        s = s + "\n  </div>\n"

    # end the last row, and container, if needed:
    if max_columns > 1:
        s = s + "\n</div>"

    # close "card-body" and "card"
    s += "\n</div></div></div>"
    return mark_safe(s)


def validate_info_url_fields(info_url, switch, interface=False):
    """
    Check that the fields used in the URL definition are set.
    Return True if set, False if not
    Currently checks nms_id and hostname, since those are not always defined.
    """

    if 'url' not in info_url.keys():
        return False
    # not check fields in the url:
    # the switch.nms_id field is optional. If used in URL, check that it is set!
    if info_url['url'].find('switch.nms_id') > -1:
        # found it, but is the value set:
        if not switch.nms_id:
            # nms_id not set, skipping this url
            return False
    # the switch.hostname field is optional. If used in URL, check that it is set!
    if info_url['url'].find('switch.hostname') > -1:
        # found it, but is the value set:
        if not switch.hostname:
            # skipping the url
            return False
    if interface:
        # there is actually nothing to check here:
        return True
    # all OK
    return True


@register.filter
def get_switch_info_url_links(switch, user):
    """
    Get the info url(s) for the switch expanded from the settings file variable
    """
    links = ''
    if settings.SWITCH_INFO_URLS:
        for info_url in settings.SWITCH_INFO_URLS:
            # if we have a url defined, make sure used fields are set:
            if not validate_info_url_fields(info_url, switch):
                continue
            template = Template(build_url_string(info_url))
            context = Context({'switch': switch})
            links += template.render(context)

    if user.is_superuser or user.is_staff:
        if settings.SWITCH_INFO_URLS_STAFF:
            for info_url in settings.SWITCH_INFO_URLS_STAFF:
                # if we have a url defined, make sure used fields are set:
                if not validate_info_url_fields(info_url, switch):
                    continue
                template = Template(build_url_string(info_url))
                context = Context({'switch': switch})
                links += template.render(context)

    if user.is_superuser and settings.SWITCH_INFO_URLS_ADMINS:
        for info_url in settings.SWITCH_INFO_URLS_ADMINS:
            # if we have a url defined, make sure used fields are set:
            if not validate_info_url_fields(info_url, switch):
                continue
            template = Template(build_url_string(info_url))
            context = Context({'switch': switch})
            links += template.render(context)

    return mark_safe(links)


@register.filter
def get_interface_info_links(switch, iface):
    """
    Get the info url(s) for the interface expanded from the settings file variable
    """
    links = ''
    if settings.INTERFACE_INFO_URLS:
        for info_url in settings.INTERFACE_INFO_URLS:
            if not validate_info_url_fields(info_url, switch, iface):
                continue
            template = Template(build_url_string(info_url))
            context = Context({'switch': switch, 'iface': iface})
            links += template.render(context)
    return mark_safe(links)


@register.filter
def get_vlan_info_links(vlan):
    """
    Get the info url(s) for the Vlan() expanded from the settings file variable
    """
    links = ''
    if settings.VLAN_INFO_URLS:
        # do this for all URLs listed:
        for info_url in settings.VLAN_INFO_URLS:
            template = Template(build_url_string(info_url))
            context = Context(
                {
                    'vlan': vlan,
                }
            )
            links += template.render(context)
    return mark_safe(links)


@register.filter
def get_ethernet_info_links(ethernet):
    """
    Get the info url(s) for the EthernetAddress() expanded from the settings file variable
    """
    links = ''
    if settings.ETHERNET_INFO_URLS:
        # do this for all URLs listed:
        for info_url in settings.ETHERNET_INFO_URLS:
            template = Template(build_url_string(info_url))
            context = Context(
                {
                    'ethernet': ethernet,
                }
            )
            links += template.render(context)
    return mark_safe(links)


@register.filter
def get_ip4_info_links(ip4_address):
    """
    Get the info url(s) for the ipv4 address (string format) expanded from the settings file variable
    """
    links = ''
    if settings.IP4_INFO_URLS:
        # do this for all URLs listed:
        for info_url in settings.IP4_INFO_URLS:
            template = Template(build_url_string(info_url))
            context = Context(
                {
                    'ip4': ip4_address,
                }
            )
            links += template.render(context)
    return mark_safe(links)


@register.filter
def get_ip6_info_links(ip6_address):
    """
    Get the info url(s) for the ipv6 address (string format) expanded from the settings file variable
    """
    links = ''
    if settings.IP6_INFO_URLS:
        # do this for all URLs listed:
        for info_url in settings.IP6_INFO_URLS:
            template = Template(build_url_string(info_url))
            context = Context(
                {
                    'ip6': ip6_address,
                }
            )
            links += template.render(context)
    return mark_safe(links)


@register.filter
def get_interface_link(switch, iface):
    """
    Return the HTML data for this interface, including status/type images, etc.
    """
    # start with up/down color for interface
    if iface.admin_status:
        info = f" bgcolor=\"{settings.BGCOLOR_IF_ADMIN_UP}\" "
    else:
        info = f" bgcolor=\"{settings.BGCOLOR_IF_ADMIN_DOWN}\" "
    # next add the NMS link for this interface
    info += get_interface_info_links(switch, iface)
    # next make linkable if we can manage it
    if iface.manageable:
        if iface.admin_status:
            info = (
                info
                + f"<a onclick=\"return confirm_change('Are you sure you want to DISABLE {iface.name} ?')\" \
                     href=\"/switches/{switch.group.id}/{switch.id}/{iface.index}/admin/0/\" \
                     data-bs-toggle=\"tooltip\" data-bs-title=\"Click here to Disable {iface.name}\">{iface.name}</a>"
            )
        else:
            info = (
                info
                + f"<a onclick=\"return confirm_change('Are you sure you want to ENABLE {iface.name} ?')\" \
                     href=\"/switches/{switch.group.id}/{switch.id}/{iface.index}/admin/1/\" \
                     data-bs-toggle=\"tooltip\" data-bs-title=\"Click here to Enable {iface.name}\">{iface.name}</a>"
            )

    else:
        info = info + f" {iface.name} "

    # start with up/down color for interface
    if iface.admin_status:
        info = (
            info
            + "&nbsp;&nbsp;<img src=\"/static/img/enabled.png\" \
                 alt=\"Interface Enabled\" data-bs-toggle=\"tooltip\" data-bs-title=\"Interface is Enabled\">"
        )
    else:
        info = (
            info
            + "&nbsp;&nbsp;<img src=\"/static/img/disabled.png\" \
                 alt=\"Interface Disabled\" data-bs-toggle=\"tooltip\" data-bs-title=\"Interface is Disabled\">"
        )

    # finally, add icons representing interface 'features'
    if iface.is_tagged:
        info = (
            info
            + "&nbsp;&nbsp;<i class=\"fas fa-ellipsis-v\" aria-hidden=\"true\" \
                 alt=\"Tagged/Trunked Interface\" data-bs-toggle=\"tooltip\" data-bs-title=\"Tagged/Trunked Interface\"></i>"
        )
    if iface.voice_vlan:
        info = (
            info
            + f"&nbsp;&nbsp;<i class=\"fas fa-phone\" aria-hidden=\"true\" \
                 alt=\"Voice VLAN\" data-bs-toggle=\"tooltip\" data-bs-title=\"Voice VLAN {iface.voice_vlan}>\""
        )

    return mark_safe(info)


def set_neighbor_icon_info(neighbor):
    """
    Set the FontAwesome icon for a neighbor device.
    To keep things simple, we set a single icon, even when multiple capabilities exist.

    Args:
        neighbor (NeighborDevice()): the neighbor device object to get info about.

    Returns:
        n/a
    """
    capabilities = neighbor.capabilities
    if capabilities == LLDP_CAPABILITIES_NONE:
        neighbor.icon = settings.NB_ICON_NONE
        neighbor.style = settings.MM_NB_STYLE_NONE
        neighbor.start_device = '['
        neighbor.stop_device = ']'
        neighbor.description = 'Capabilities NOT Advertized'
        return
    if capabilities & LLDP_CAPABILITIES_WLAN:
        neighbor.icon = settings.NB_ICON_WLAN
        neighbor.style = settings.MM_NB_STYLE_WLAN
        neighbor.start_device = '(['
        neighbor.stop_device = '])'
        neighbor.description = 'Wireless AP'
        return
    if capabilities & LLDP_CAPABILITIES_PHONE:
        neighbor.icon = settings.NB_ICON_PHONE
        neighbor.style = settings.MM_NB_STYLE_PHONE
        neighbor.start_device = '('
        neighbor.stop_device = ')'
        neighbor.description = 'VOIP Phone'
        return
    if capabilities & LLDP_CAPABILITIES_ROUTER:
        neighbor.icon = settings.NB_ICON_ROUTER
        neighbor.style = settings.MM_NB_STYLE_ROUTER
        neighbor.start_device = '['
        neighbor.stop_device = ']'
        neighbor.description = 'Router or Switch'
        return
    if capabilities & LLDP_CAPABILITIES_STATION:
        neighbor.icon = settings.NB_ICON_STATION
        neighbor.style = settings.MM_NB_STYLE_STATION
        neighbor.start_device = '('
        neighbor.stop_device = ')'
        neighbor.description = 'Workstation or Server'
        return
    if capabilities & LLDP_CAPABILITIES_BRIDGE:
        # We only show Switch if no routing or phone capabilities listed.
        # Most phones and routers also show switch capabilities.
        # In those cases we only show the above Router or Phone icons!
        neighbor.icon = settings.NB_ICON_BRIDGE
        neighbor.style = settings.MM_NB_STYLE_BRIDGE
        neighbor.start_device = '['
        neighbor.stop_device = ']'
        neighbor.description = 'Switch'
        return
    if capabilities & LLDP_CAPABILITIES_REPEATER:
        neighbor.icon = settings.NB_ICON_REPEATER
        neighbor.style = settings.MM_NB_STYLE_REPEATER
        neighbor.start_device = '['
        neighbor.stop_device = ']'
        neighbor.description = 'Hub or Repeater'
        return
    # unlikely to see this!
    # elif capabilities & LLDP_CAPABILITIES_DOCSIS:
    #    icon = "unknown"
    if capabilities & LLDP_CAPABILITIES_OTHER:
        neighbor.icon = settings.NB_ICON_OTHER
        neighbor.style = settings.MM_NB_STYLE_OTHER
        neighbor.start_device = '('
        neighbor.stop_device = ')'
        neighbor.description = 'Other Capabilities'
        return


@register.filter
def get_lldp_info(neighbor):
    """
    Return an hmtl img string that represents the lldp neighbor device and capabilities
    """

    icon = ''
    # add an image for the capabilities
    icon_format = "<i class=\"fas %s\" data-bs-toggle=\"tooltip\" data-bs-title=\"%s\"></i>&nbsp;"
    capabilities = neighbor.capabilities
    if capabilities == LLDP_CAPABILITIES_NONE:
        icon = icon_format % ('fa-question', 'Capabilities NOT Advertized')
    else:
        if capabilities & LLDP_CAPABILITIES_WLAN:
            icon += icon_format % ('fa-wifi', 'Wireless AP')
        if capabilities & LLDP_CAPABILITIES_PHONE:
            icon += icon_format % ('fa-phone', 'VOIP Phone')
        if capabilities & LLDP_CAPABILITIES_ROUTER:
            icon += icon_format % ('fa-cogs', 'Router or Switch')
        if capabilities & LLDP_CAPABILITIES_STATION:
            icon += icon_format % ('fa-desktop', 'Workstation or Server')
        if (
            capabilities & LLDP_CAPABILITIES_BRIDGE
            and not capabilities & LLDP_CAPABILITIES_ROUTER
            and not capabilities & LLDP_CAPABILITIES_PHONE
        ):
            # We only show Switch if no routing or phone capabilities listed.
            # Most phones and routers also show switch capabilities.
            # In those cases we only show the above Router or Phone icons!
            icon += icon_format % ('fa-ethernet', 'Switch')
        if capabilities & LLDP_CAPABILITIES_REPEATER:
            icon += icon_format % ('fa-ethernet', 'Hub or Repeater')
        # elif capabilities & LLDP_CAPABILITIES_DOCSIS:
        # unlikely to see this!
        #    icon = "unknown"
        if capabilities & LLDP_CAPABILITIES_OTHER:
            icon += icon_format % ('fa-question', 'Other Capabilities')

    if neighbor.hostname:
        name = f"{neighbor.hostname} "
    elif neighbor.sys_name:
        name = f"{neighbor.sys_name} "
    else:
        name = ""

    if neighbor.port_name:
        port = f"({neighbor.port_name}) "
    else:
        port = ""

    if neighbor.chassis_string:
        chassis = f" - {neighbor.chassis_string}"
    else:
        chassis = ""

    if neighbor.sys_descr or neighbor.management_address:
        if neighbor.management_address:
            mgmt = f"Mgmt IP: {neighbor.management_address}&#10;&#13;"  # lf/cr may not be supported by all browsers.
        else:
            mgmt = ""
        info = f"{icon}<abbr data-bs-toggle=\"tooltip\" data-bs-title=\"{mgmt}{neighbor.sys_descr}\">{name}{port}{chassis}</abbr>"
    else:
        info = f"{icon}{name}{port}{chassis}"

    return mark_safe(info)


@register.filter
def get_neighbor_mermaid_config(neighbor):
    """
    Return a string that represents the lldp neighbor for a mermaid.js graph.
    To keep things simple, we return a single icon, even when multiple capabilities exist.
    """

    if neighbor.hostname:
        neighbor.name = neighbor.hostname
    elif neighbor.sys_name:
        neighbor.name = neighbor.sys_name
    else:
        neighbor.name = "Unknown System"

    set_neighbor_icon_info(neighbor)

    mermaid = f"{neighbor.index}{neighbor.start_device}\"fa:{neighbor.icon} {neighbor.name}\n"
    if neighbor.port_name:
        mermaid = f"{mermaid}({neighbor.port_name})"
    mermaid = f"{mermaid}\"{neighbor.stop_device}\n"
    if neighbor.style:
        mermaid = f"{mermaid}style {neighbor.index} {neighbor.style}\n"
    return mark_safe(mermaid)


@register.filter
def get_poe_pse_status(status):
    """
    Return the string representing the PSE STATUS
    """
    if status == POE_PSE_STATUS_ON:
        return 'On'
    if status == POE_PSE_STATUS_OFF:
        return 'Off'
    if status == POE_PSE_STATUS_FAULT:
        return 'Faulty'
    return 'Unknown'


@register.filter
def get_options_from_comma_string(csv_values):
    """
    Return an HTML string with select options for the defined CommandTemplate() pick list.
    The 'csv_values' string can be simple comma-separated, or
    full-blown CSV encoded values, eg. "some , value", "2", "3,4,5"
    So we use the CSV reader to parse this.
    """
    # dprint(f"get_options_from_comma_string({csv_values})")
    choices = ""
    if '"' not in csv_values:
        # dprint("Regular comma-separated...")
        # regular comma-separated
        options = csv_values.split(',')
        for item in options:
            # dprint(f"ITEM={item}")
            choices += f"<option value=\"{item}\">{item}</option>\n"
    else:
        # parse with CSV reader:
        # dprint("Quoted string")
        reader = csv.reader(csv_values, skipinitialspace=True)
        for row in reader:
            # dprint(f"ROW={type(row)}: {row}")
            for item in row:
                if item:
                    # dprint(f"ITEM={item}")
                    choices += f"<option value=\"{item}\">{item}</option>\n"
    return mark_safe(choices)


@register.filter
def list_ip_addresses(iface: Interface) -> str:
    """List all IP address associated with an Interface()
    iface (Interface)
    """
    s = ''
    if iface.addresses_ip4:
        for ip, addr in iface.addresses_ip4.items():
            s += f"{addr.ip}/"
            if settings.IFACE_IP4_SHOW_PREFIXLEN:
                s += f"{addr.prefixlen}"
            else:
                s += f"{addr.netmask}"
    # ipv6 tbd
    # if iface.addresses_ip6:
    #     for ip,addr in iface.addresses_ip4.items():
    #         s += f"{addr.ip}/"
    #         if settings.IFACE_IP4_SHOW_PREFIXLEN:
    #             s += f"{addr.prefixlen}"
    #         else:
    #             s += f"{addr.netmask}"
    return s


@register.simple_tag()
def querystring(request, **kwargs):
    """
    Append or update the page number in a querystring.
    """
    querydict = request.GET.copy()
    for k, v in kwargs.items():
        if v is not None:
            querydict[k] = str(v)
        elif k in querydict:
            querydict.pop(k)
    querystring = querydict.urlencode(safe='/')
    if querystring:
        return '?' + querystring
    else:
        return ''


# adopted from Netbox!
@register.filter()
def humanize_speed(iface):
    """
    Humanize speeds given in Mbps. Examples:

        1 => "1 Mbps"
        100 => "100 Mbps"
        10000 => "10 Gbps"
    """
    if not iface.speed:
        return ''
    speed = iface.speed
    if iface.duplex == IF_DUPLEX_FULL:
        duplex = '/Full'
    elif iface.duplex == IF_DUPLEX_HALF:
        duplex = '/Half'
    else:
        duplex = ''
    if speed >= 1000000000 and speed % 1000000000 == 0:
        return f'{int(speed / 1000000000)} Pbps{duplex}'
    elif speed >= 1000000 and speed % 1000000 == 0:
        return f'{format(int(speed / 1000000))} Tbps{duplex}'
    elif speed >= 1000 and speed % 1000 == 0:
        return f'{format(int(speed / 1000))} Gbps{duplex}'
    elif speed >= 1000:
        return f'{format(float(speed) / 1000)} Gbps{duplex}'
    else:
        return f'{format(speed)} Mbps{duplex}'


# adopted from Netbox!
@register.filter()
def humanize_power(power):
    """
    Humanize power given in milliWatts. Examples:
        6500 => "6.5W"
        400 => "0.4W"
    """
    if not power:
        return ''
    return '{:.1f}W'.format(power / 1000)


# from https://stackoverflow.com/questions/2751319/is-there-a-django-template-filter-to-display-percentages
@register.filter
def as_percentage_of(part, whole):
    if whole == 0:
        return "0%"
    try:
        return "%d%%" % (float(part) / whole * 100)
    except (ValueError, ZeroDivisionError):
        return "0%"
    return "unknown %"

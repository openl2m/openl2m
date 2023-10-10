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
import json

from django.conf import settings
from django import template
from django.template import Template, Context
from django.utils.html import mark_safe

from switches.models import SwitchGroupMembership
from switches.constants import SWITCH_STATUS_ACTIVE, SWITCH_VIEW_BASIC, SWITCH_VIEW_DETAILS
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

# see https://docs.djangoproject.com/en/2.2/ref/templates/api/
# and https://docs.djangoproject.com/en/2.2/howto/custom-template-tags/

register = template.Library()


def build_url_string(values):
    """
    Build a external url string from the url values dict() given
    Used to build custom links from "settings" variables
    """
    if 'target' in values.keys():
        s = f"<a target=\"{values['target']}\" "
    else:
        s = "<a "
    s = s + f"href=\"{values['url']}\""
    if 'hint' in values.keys():
        s = s + f"data-toggle=\"tooltip\" title=\"{values['hint']}\""
    s = s + ">"
    if 'fa_icon' in values.keys():
        s = s + f"<i class=\"fas {values['fa_icon']}\" aria-hidden=\"true\"></i>"
    elif 'icon' in values.keys():
        s = s + f"<img src=\"{values['icon']}\" alt=\"{values['alt']}\" height=\"24\" width=\"24\">"
    s = s + "</a> "
    return s


def get_switch_link(group, switch):
    """
    Build custom html link to switch, based on switch attributes
    """
    s = "<li class=\"list-group-item\">"
    if switch.description:
        s = s + f"<span data-toggle=\"tooltip\" data-placement=\"auto bottom\" title=\"{switch.description}\">"
    # do proper indenting:
    indent = ''
    for i in range(switch.indent_level):
        indent = indent + "&nbsp;&nbsp;&nbsp;"
    if switch.default_view == SWITCH_VIEW_BASIC:
        s = s + f"{indent}<a href=\"/switches/{group.id}/{switch.id}/\">"
    else:
        s = s + f"<a href=\"/switches/{group.id}/{switch.id}/details/\">"
    s = s + f"{switch.name}</a>"
    if switch.description:
        s = s + "</span>"
    s = s + "</li>"
    return s


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
        if description:
            tooltip = f"<abbr data-toggle=\"tooltip\" data-placement=\"auto bottom\" title=\"{description}\">"
            tt_end = "</abbr>"
        else:
            tooltip = tt_end = ""
        link = f"\n<li class=\"list-group-item\">{tooltip}<a href=\"/switches/{group_id}/{switch_id}/"
        if default_view == SWITCH_VIEW_DETAILS:
            link += "details/"
        if group_count > 1:
            found += f"{link}\">{name}</a>{tt_end} ({group_name})</li>"
        else:
            found += f"{link}\">{name}</a>{tt_end}</li>"

    return mark_safe(f"<ul class=\"list-group\">{found}</ul>\n")


@register.filter
def get_my_switchgroups(groups):
    """
    Build custom html menu of all the switchgroups and their switches
    """
    num_groups = len(groups)
    if not num_groups:
        s = "<strong>You are not a member of any switch groups!</strong></br>Please contact the OpenL2M administrator!\n"
        return mark_safe(s)
    # at least one group:
    s = '<div class="row"><div class="col-sm-6 col-md-4">'
    if num_groups == 1:
        # one group only
        s = s + "\n<h4>My Switch Group:</h4>"
    else:
        s = s + "\n<h4>My Switch Groups:</h4>"

    # start groups wrapper:
    s = s + "\n</div></div>"  # end header row

    # calculate column width, if set. Bootstrap uses 12 grid columns per page, max we use is 3 grids
    col_width = 3
    if settings.TOPMENU_MAX_COLUMNS > 4:
        col_width = int(12 / settings.TOPMENU_MAX_COLUMNS)

    # now list the groups:
    group_num = 0
    for group_name, group in groups.items():
        group_num += 1
        if settings.TOPMENU_MAX_COLUMNS > 1:
            if not ((group_num - 1) % settings.TOPMENU_MAX_COLUMNS):
                # end previous row, if needed
                if group_num > 1:
                    s = s + "\n</div>"
                # and start a new row!
                s = s + "\n\n<div class=\"row\">"
            # add column div:
            s = s + f"\n <div class=\"col-md-{col_width}\">"
        else:
            s = s + f"\n <div class=\"row\">\n  <div class=\"col-md-{col_width}\">"
        # header for collapsible items, i.e. the switchgroup name
        s = (
            s
            + "\n  <div class=\"panel-group\">\n   <div class=\"panel panel-default\">\n   <div class=\"panel-heading\">"
        )
        s = s + f"<a data-toggle=\"collapse\" href=\"#group{group.id}\">"
        if group.description:
            s = s + f"\n  <span data-toggle=\"tooltip\" title=\"{group.description}\">"
        if group.display_name:
            s = s + group.display_name
        else:
            s = s + group.name
        if group.description:
            s = s + "</span>"
        s = s + "</a>"
        if group.read_only:
            s = s + " (r/o)"
        s = s + "</div>"  # this /div ends panel-heading

        # the collapsible items:
        s = s + f"\n   <div id=\"group{group.id}\" class=\"panel-collapse"
        # if only 1 group, show all items
        if num_groups > 1:
            s = s + " collapse"
        s = s + "\">\n    <ul class=\"list-group\">"
        for member in SwitchGroupMembership.objects.filter(switchgroup=group):
            if member.switch.status == SWITCH_STATUS_ACTIVE:
                s = s + f"\n    {get_switch_link(group, member.switch)}"
        s = s + "\n    </ul>\n   </div>"  # /div ends panel-collapse

        # and end this group header and group:
        s = s + "\n  </div>\n  </div>"  # end panel-default and panel-group

        if settings.TOPMENU_MAX_COLUMNS > 1:
            # end the column div:
            s = s + "\n </div>"
        else:
            # end row
            s = s + "\n </div>\n</div>"  # end panel-default and panel-group

    # end the last row, and container, if needed:
    if settings.TOPMENU_MAX_COLUMNS > 1:
        s = s + "\n</div>"

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
                     data-toggle=\"tooltip\" title=\"Click here to Disable {iface.name}\">{iface.name}</a>"
            )
        else:
            info = (
                info
                + f"<a onclick=\"return confirm_change('Are you sure you want to ENABLE {iface.name} ?')\" \
                     href=\"/switches/{switch.group.id}/{switch.id}/{iface.index}/admin/1/\" \
                     data-toggle=\"tooltip\" title=\"Click here to Enable {iface.name}\">{iface.name}</a>"
            )

    else:
        info = info + f" {iface.name} "

    # start with up/down color for interface
    if iface.admin_status:
        info = (
            info
            + "&nbsp;&nbsp;<img src=\"/static/img/enabled.png\" \
                 alt=\"Interface Enabled\" data-toggle=\"tooltip\" title=\"Interface is Enabled\">"
        )
    else:
        info = (
            info
            + "&nbsp;&nbsp;<img src=\"/static/img/disabled.png\" \
                 alt=\"Interface Disabled\" data-toggle=\"tooltip\" title=\"Interface is Disabled\">"
        )

    # finally, add icons representing interface 'features'
    if iface.is_tagged:
        info = (
            info
            + "&nbsp;&nbsp;<i class=\"fas fa-ellipsis-v\" aria-hidden=\"true\" \
                 alt=\"Tagged/Trunked Interface\" data-toggle=\"tooltip\" title=\"Tagged/Trunked Interface\"></i>"
        )
    if iface.voice_vlan:
        info = (
            info
            + f"&nbsp;&nbsp;<i class=\"fas fa-phone\" aria-hidden=\"true\" \
                 alt=\"Voice VLAN\" data-toggle=\"tooltip\" title=\"Voice VLAN {iface.voice_vlan}>\""
        )

    return mark_safe(info)


@register.filter
def get_lldp_info(neighbor):
    """
    Return an hmtl img string that represents the lldp neighbor device and capabilities
    To keep things simple, we return a single icon, even when multiple capabilities exist.
    """

    info = ''
    # add an image for the capabilities
    fa_format = "<i class=\"fas %s\" data-toggle=\"tooltip\" title=\"%s\"></i>&nbsp;"
    capabilities = neighbor.capabilities
    if capabilities == LLDP_CAPABILITIES_NONE:
        info += fa_format % ('fa-question', 'Capabilities NOT Advertized')
    else:
        if capabilities & LLDP_CAPABILITIES_WLAN:
            info += fa_format % ('fa-wifi', 'Wireless AP')
        if capabilities & LLDP_CAPABILITIES_PHONE:
            info += fa_format % ('fa-phone', 'VOIP Phone')
        if capabilities & LLDP_CAPABILITIES_ROUTER:
            info += fa_format % ('fa-cogs', 'Router or Switch')
        if capabilities & LLDP_CAPABILITIES_STATION:
            info += fa_format % ('fa-desktop', 'Workstation or Server')
        if (
            capabilities & LLDP_CAPABILITIES_BRIDGE
            and not capabilities & LLDP_CAPABILITIES_ROUTER
            and not capabilities & LLDP_CAPABILITIES_PHONE
        ):
            # We only show Switch if no routing or phone capabilities listed.
            # Most phones and routers also show switch capabilities.
            # In those cases we only show the above Router or Phone icons!
            info += fa_format % ('fa-ethernet', 'Switch')
        if capabilities & LLDP_CAPABILITIES_REPEATER:
            info += fa_format % ('fa-ethernet', 'Hub or Repeater')
        # elif capabilities & LLDP_CAPABILITIES_DOCSIS:
        # unlikely to see this!
        #    icon = "unknown"
        if capabilities & LLDP_CAPABILITIES_OTHER:
            info += fa_format % ('fa-question', 'Other Capabilities')

    name = ''
    if neighbor.sys_name:
        name = neighbor.sys_name
    else:
        name = 'Unknown'

    if neighbor.sys_descr or neighbor.hostname:
        if neighbor.hostname:
            hostname = neighbor.hostname + " - "
        else:
            hostname = ""
        info = f"{info}<abbr data-toggle=\"tooltip\" title=\"{hostname}{neighbor.sys_descr}\">{name}"
        if neighbor.chassis_string:
            info = f"{info} - {neighbor.chassis_string}"
        info = info + "</abbr>"
    else:
        info = f"{info}{name}"
        if neighbor.chassis_string:
            info = f"{info} - {neighbor.chassis_string}"

    return mark_safe(info)


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
def get_options_from_comma_string(comma_string):
    """
    Return an HTML string with select options for the defined CommandTemplate() pick list.
    """
    choices = ""
    options = comma_string.split(',')
    for val in options:
        v = val.strip()
        choices += f"<option value=\"{v}\">{v}</option>\n"
    return mark_safe(choices)


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
    try:
        return "%d%%" % (float(part) / whole * 100)
    except (ValueError, ZeroDivisionError):
        return ""

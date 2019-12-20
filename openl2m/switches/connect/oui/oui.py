from switches.connect.oui.oui_dict import *


def get_vendor_from_oui(oui):
    """
    Return the ethernet vendor from the given OUI strings
    """
    if oui in oui_to_vendor.keys():
        return oui_to_vendor[oui]
    return ''

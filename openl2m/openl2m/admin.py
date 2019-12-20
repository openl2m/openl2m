from django.conf import settings
from django.contrib.admin import AdminSite

# Create a custom Admin site.
# NOTE: User admin is registered in the users/ application!


class OpenL2MAdminSite(AdminSite):
    """
    Custom admin site
    """
    site_header = 'OpenL2M Administration'
    site_title = 'OpenL2M'
    site_url = '/{}'.format(settings.BASE_PATH)


# create new admin site
admin_site = OpenL2MAdminSite(name='admin')

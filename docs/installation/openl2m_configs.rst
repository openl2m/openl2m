.. image:: ../_static/openl2m_logo.png

==============================
OpenL2M Optional Configuration
==============================

This section discusses some of optional parts of the *configuration.py* file.
**Note that NOT ALL options are documented here.** Please read *configuration.example.py* for the complete
list of options. Loggged in as admin, you can see the active list of configuration settings from your drop-down menu.

**You can skip this section if you are not interested in tailoring settings.**

Banners
-------

Text to include on the login page above the login form can be set here. You can use this to set warnings, etc. HTML is allowed.

**BANNER_LOGIN** = 'Unauthorized use is Prohibited. <strong>All Activity is logged and monitored.</strong>'

Optionally you can display a persistent banner at the top and/or bottom of every page. HTML is allowed. To display the same
content in both banners, define BANNER_TOP and set BANNER_BOTTOM = BANNER_TOP.

**BANNER_TOP** = 'Top Banner Information Line'

**BANNER_BOTTOM** = 'Bottom Banner Line'


Logging to Syslog
-----------------

You can select to send OpenL2M activity logs to a "syslog host". You will need to set the following entries:

**SYSLOG_HOST** = 'localhost'

If SYSLOG_HOST is defined (default=False), log entries will also be sent here, to the 'user' facility.

If needed, you can change the UDP port:

**SYSLOG_PORT** = 514

By default SYSLOG_JSON=True, and syslog entries will be send in Json format for easier parsing.
If False, a textual version of log event will be sent.

**SYSLOG_JSON** = True


Link State Colors
-----------------

You can change the background colors of the Interface Admin-Down, Admin-Up (up/down), and Operational-Up (up/up) states.

We defined html colors as shown here. A great place for colors: https://www.rapidtables.com/web/color/

Admin disabled (red):  **BGCOLOR_IF_ADMIN_DOWN** = "#EB5B5B"

Admin-UP, No Link (darker light green):  **BGCOLOR_IF_ADMIN_UP** = "#98FB98"

Admin-UP, Link UP (bright green):  **BGCOLOR_IF_ADMIN_UP_UP** = "#ADFF2F"


Email settings
--------------

Selected log entries and errors can be sent via email if the following are set. Set the name of your email (relay) server here:

**EMAIL_HOST** = 'localhost'

If authentication to the EMAIL_HOST server is needed, set the following:

**EMAIL_HOST_USER** = ''

**EMAIL_HOST_PASSWORD** = ''

The ADMIN setting is used for OpenL2M "administrator" emails. This is a list of all the people who get code error notifications,
and other emails (see below). This is not related to users with superuser access.

**ADMINS** = [
    # ('John', 'john@example.com'),

    # ('Mary', 'mary@example.com')

]



Next, configure the REST API as needed, and then finalize the installation.

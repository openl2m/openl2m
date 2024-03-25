.. image:: ../_static/openl2m_logo.png

HTML Layout
===========

We use Bootstrap for HMTL layout. Below are some quick notes about how we use Bootstrap 5 through the HTML layout of OpenL2M.

Any changes to HMTL layout should use Bootstrap, and should adhere to modern Web Content Accesibility Guidelines (WCAG).

See more at https://www.w3.org/WAI/standards-guidelines/wcag/

A useful tool during development is the "WAVE Web Accesibility Evaluation Tool" browser extension.


Positioning
-----------

Most pages and segments use the <div class "container-fluid"> construct to get a 100% wide page on all devices.

Additionally, we can use positioning to line up along the top of the page:

See more at https://getbootstrap.com/docs/5.3/utilities/position/

Row and column
--------------

Bootstrap has a "row" and "col" concept. These are heavily used throughout the HTML pages.
In Bootstrap 5, there are "12" columns per row, and we can define specific widths with "col-3":
this is a column with a width of about 25% of the screen.

We use various "div" options to adjust layout in each "row", *<div class="row justify-content-md-center">*

See more at https://getbootstrap.com/docs/5.3/layout/grid/

Start and End
-------------

Bootstrap 5 uses "start" and "end", instead of "left" and "right".
E.g. "me-auto" is "Marging-End Auto", ie automatic right side margin.

mb- is Margin Bottom

See more at https://getbootstrap.com/docs/5.3/utilities/spacing/

Menus
-----

Dropdowns are described at https://getbootstrap.com/docs/5.3/components/dropdowns/


Tooltips
--------

We use the tooltips from Bootstrap, as such:

    **data-bs-toggle="tooltip" data-bs-title="Tooltip text here"**

This is initiated in _base.html, in the **$(document).ready(function())**, per this page:

https://getbootstrap.com/docs/5.3/components/tooltips/#overview


Tab Menus
---------

Tab Menus are implemented as documented here: https://fastbootstrap.com/components/tabs/

They are implemented in *openl2m/templates/switch.html* which includes calls various *_menu_<name>.html*

Since we use templates for the various tab menu, and some need to be active or not, we include
these templates as such in *switch.html*:

.. code-block:: jinja

    {% include "_menu_interfaces.html" with state="active" %}

and in the _menu_<name>.html as such:

.. code-block:: jinja

  <a
   href="#tab_arp_lldp"
   data-bs-toggle="tab"
   class="nav-link {{ state }}"


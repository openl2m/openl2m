.. image:: ../../_static/openl2m_logo.png

==============================
Showing Neighbors Graphically.
==============================

We can graph the neighbors from the Arl/LLDP tab of the device view. This uses the Mermaid Javascript library.
See https://mermaid.js.org/config/usage.html

In the ARP/LLDP tab html (in *templates/_tab_if_arp_lldp.html*) we render an link as *<a id="openGraphButton">*
At the bottom, we include *_neighbor_mermaid_graphic.html*

*_neighbor_mermaid_graphic.html* adds a *<script>* tag to the page with a click-handler for the above link:

.. code-block:: Javascript

    document.getElementById('openGraphButton').addEventListener('click', function() {

In this function, we generate a new window, and add html code for the Mermaid graph.

A little bit of logic creates a horizontal graph for a few neighors, or a vertical graph for many.

.. code-block:: Javascript

    {% if connection.neighbor_count <= settings.NB_MAX_FOR_TD %}
        flowchart TD
    {% else %}
        flowchart LR
    {% endif %}

Next we loop through all interfaces and neighbors, and call the function *get_neighbor_mermaid_config()*
to create the Mermaid code for each neighbor connection. This is implemented in *switches/templatetags/helpers.py*

Finally, we stuff the Mermaid javascript code into the page, and close the new page to let the browser load it.
Note that this new page is "coded inside the regular main html page"!

The final 'stuffing' of the js code is needed, as inline coding with <script>mermaid.js</script> confuses
browser parsing engines; they take the </script> as part of the "mother page" and this breaks things...
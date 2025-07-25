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
This calls python code from the *switches/templatetags/helpers.py* files:

.. code-block:: html

  {% load helpers %}
  ...
  <pre class="mermaid">
    {{ connection|get_neighbor_mermaid_graph }}
  </pre>


The function *get_neighbor_mermaid_graph()* loops through all interfaces and neighbors,
to create the Mermaid code for each neighbor connection. (in switches/templatetags/helpers.py)

Finally, if neighbors found, we stuff the Mermaid javascript code into the page, and close the new page to let the browser load it.
Note that this new page is "coded inside the regular main html page"!

At the end of *_tab_if_arp_lldp.html*:

.. code-block:: jinja

    {% if connection.neighbor_count > 0 %}
        {% include "_neighbor_mermaid_graphic.html" %}
    {% endif %}


The final 'stuffing' of the js code is needed, as inline coding with <script>mermaid.js</script> confuses
browser parsing engines; they take the </script> as part of the "mother page" and this breaks things...
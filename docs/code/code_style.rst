.. image:: ../_static/openl2m_logo.png

==========
Code Style
==========

We welcome code additions, via Git Pull-Requests, or email, or whatever fashion works for you!

We use *black* to enforce the code style. For more details see
https://black.readthedocs.io/en/stable/usage_and_configuration/the_basics.html

To document functions and classes, we use the Google comment style, see more at
https://google.github.io/styleguide/pyguide.html

New code should add Python type hinting. Specifically, we require type hints as documented in
`PEP 484 <https://peps.python.org/pep-0484/>`_ and variable annotations per `PEP 526. <https://peps.python.org/pep-0526/>`_
(We are working on retrofitting existing 3.x code!)

Function calls with more then one parameter should use named parameters, instead of position-based calling.

HTML
----

All HTML should be validated by the W3 validator at https://validator.w3.org/#validate_by_input


Accessibility
-------------

Accessibility should be tested by using the WAVE Web Accessibility Evaluation Tool browser extension.
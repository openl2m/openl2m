.. image:: ../_static/openl2m_logo.png

Maintaining the documentation
=============================

**Sphinx and Restructured Text**

The documentation for OpenL2M lives under */docs*,
and is written in ReStructuredText. We use the Sphinx documentation
generator to generate our html pages, which are live available in the
application at *<your_base_url>/static/docs/*

`See this page for a Sphynx tutorial. <https://matplotlib.org/sampledoc/>`_

We installed::

  pip3 install sphinx

**Sphinx configuration**

We started with running "sphinx-quickstart" in the *docs/* directory.
Next, we updated the */docs/Makefile* to create the 'build' html files
in */openl2m/project-static/docs/*

**Build most recent documentation**

To manually test documentation updates, from the */docs* directory, run 'make html'.
This deletes existing html files, and generates new files.

When you run the 'update.sh' script, this will also create the new documentation html files,
and then these will be moved with all other project updates.

**Editing documentation**

We use the `Atom editor <https://atom.io>`_
Here is `a quick cheat sheet to RestructuredText
<https://thomas-cokelaer.info/tutorials/sphinx/rest_syntax.html>`_

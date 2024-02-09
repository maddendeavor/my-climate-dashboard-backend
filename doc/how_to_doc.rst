How-To do Sphinx docs
=====================

This article provides a very quick overview of writing, compiling, and validating sphinx docs.

General resources for Python documentation

https://devguide.python.org/documenting/

Resources on sphinx can be found at

http://www.sphinx-doc.org/en/master/

and for reStructuredText (reST) at

http://docutils.sourceforge.net/docs/user/rst/quickstart.html


Setup
-----

Required packages::
~~~~~~~~~~~~~~~~~~~

    sphinx

    sphinx-readable-theme

    sphinxcontrib-napoleon


First make
~~~~~~~~~~

If the docs haven't been built before in this repo, the first step is to build the docs from the ``doc/`` directory::

    $ make html

If no errors occur, the compiled html will be located within ``doc/_build/html``


HTTP Server
~~~~~~~~~~~

To test if the html compiles as expected, the built-in python ``SimpleHTTPServer`` can be run from the directory containing the documentation.

Example::

    $ cd {python-project}
    $ python -m SimpleHTTPServer   # NOTE: this is actually python2.7 here

The html is now being served at the machine from port 8000 and can be viewed from firefox by visiting the url at ``your-machine-ip:8000``


Iterate
-------

After the initial setup the workflow is

*   Edit the restructuredText (reST) source files or the python docstrings

*   Compile the html

*   Refresh the page and verify

.. IPyMake documentation master file, created by
   sphinx-quickstart on Mon Dec 14 21:46:02 2009.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

IPyMake -- Production Language Extention for IPython
====================================================

Contents:

.. toctree::
   :maxdepth: 2

Overview
=========

IPyMake was created because of the need for a simple, flexible and
extensible build tool. The Python language and syntax is ideal because
it relatively easy for any one programmer to learn in short
while. Incorporating a production tool with Python creates an object
oriented build language that is easy to understand and use while not
losing the power of other higher level tools.

It is common for other configuration tools (i.e. GNU Autotools and
CMake) to translate the input language into an actual Makefile that is
then executed by Make. These tools also have the nasty habit of
encoding a lot of their function through their higher level
abstractions leaving thier users at a loss when unexpected behaviour
occurs. Other build tools, on the other hand, offer a limited scope of
build targets, or use a verbose syntax. Python's own distutils is
extremely powerful within the Pythonic realm and the same for Apache
Ant in the Java domain, albeit overly verbose XML.

IPyMake aims to curb these problems by offering a managed build
environment under which the user can access any command on the system,
transparency or operation to state what is being done, ease of use
thanks to Python, and beacuse it is written in Python you can debug
the build language with PDB.





Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


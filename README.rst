git-index
=========

[![Build Status](https://travis-ci.org/TronPaul/git-index.svg?branch=master)](https://travis-ci.org/TronPaul/git-index)

*Index Git commit diffs and metadata into Elasticsearch*

Installation
------------

* Run::

    $ python setup.py install

Configuration
-------------

git-index looks for a ``[git-index]`` block in the Git configuration. The current
configuration options are:

* ``host`` - the hostname of the Elasticsearch server(s) you wish to use
* ``index`` (optional) - the name of the index you wish to use (git-index will
  default to the name of the origin repo if not specified)

Example::

    [git-index]
        host = localhost
        host = some-remote-host:9456
        index = my-repo

Usage
-----

* See ``git-index --help`` for up to date usage

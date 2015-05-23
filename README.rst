aio.web.page
============

Web server for the aio_ asyncio framework

.. _aio: https://github.com/phlax/aio



Build status
------------

.. image:: https://travis-ci.org/phlax/aio.web.page.svg?branch=master
	       :target: https://travis-ci.org/phlax/aio.web.page


Installation
------------

Requires python >= 3.4 to work

Install with:

.. code:: bash

	  pip install aio.web.page


Quick start - hello world web page
----------------------------------

Create a web server that serves a hello world page

Save the following into a file "hello.conf"

.. code:: ini

	  [aio]
	  modules = aio.web.server

	  [server/my_server]
	  factory = aio.web.server.factory
	  port = 8080

	  [web/my_server]
	  template_dirs = templates
	  
	  [web/my_server/my_route]
	  match = /
	  route = my_example.handler


And save the following into a file named "my_example.py"

.. code:: python

	  import aiohttp
	  import aio.web.server

	  @aio.web.server.route('example_page.html')
	  def handler(request, config):
	      return {"message": "Hello template world"}


And the following into a file named "templates/example_page.html"

.. code:: html
	  <html>
	    <body>
	      {{ message }}
	    </body>
	  </html>
	    
Run with the aio run command

.. code:: bash

	  aio run -c hello.conf

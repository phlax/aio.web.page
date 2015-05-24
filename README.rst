aio.web.page
============

Web page templates for the aio_ asyncio framework

.. _aio: https://github.com/phlax/aio



Build status
------------

.. image:: https://travis-ci.org/phlax/aio.web.page.svg?branch=master
	       :target: https://travis-ci.org/phlax/aio.web.page


Installation
------------

Requires python >= 3.4

Install with:

.. code:: bash

	  pip install aio.web.page


Quick start - hello world web page
----------------------------------

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
	  route = my_example.route_handler


And save the following into a file named "my_example.py"

.. code:: python

	  import aio.web.page	  
	  import aio.web.server

	  @aio.web.page.template('example_page.html')
	  def template_handler(request):
	      return {"message": "Hello template world"}	  
	  
	  @aio.web.server.route
	  def route_handler(request, config):
	      return (yield from template_handler(request))


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


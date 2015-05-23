aio.web.server usage
--------------------


Configuration
-------------

Let's create a config defining a factory method and using the aio.web.server.protocol for the protocol

In the following configuration example a server named "example-1" is set up.

Any sections that start with "web/example-1/" will be treated as route definitions.

The route definition should provide a "match" and a "route" at a minimum.

The route is given a name derived from the section name. In this case "homepage"

To set up the web server, we need to:

- add "aio.web.server" to aio:modules initialize the web server
- add a server/SERVERNAME section to create the http server
- add a web/SERVERNAME/ROUTENAME to create a route

Lets create a basic web server configuration
  
  >>> web_server_config = """
  ... [aio]
  ... log_level = ERROR
  ... modules = aio.web.server
  ... 
  ... [server/server_name]
  ... factory = aio.web.server.factory
  ... port = 7070
  ... 
  ... [web/server_name/route_name]
  ... match = /
  ... route = aio.web.server.tests._example_handler
  ... """  

Now lets create a route and make it importable
 
  >>> import asyncio
  >>> import aiohttp
  >>> import aio.web.server.tests

  >>> @asyncio.coroutine
  ... def handler(request):
  ...     return aiohttp.web.Response(body=b"Hello, web world")    

  >>> aio.web.server.tests._example_handler = handler

Lets set up a test to run the server and request a web page
  
  >>> from aio.app.runner import runner    
  >>> from aio.testing import aiofuturetest

  >>> @aiofuturetest(sleep=1)
  ... def run_web_server(config, request_page="http://localhost:7070"):
  ...     yield from runner(['run'], config_string=config)
  ... 
  ...     def call_web_server():
  ...         result = yield from (
  ...             yield from aiohttp.request(
  ...                "GET", request_page)).read()
  ... 
  ...         print(result.decode())
  ... 
  ...     return call_web_server

And run the test
  
  >>> run_web_server(web_server_config)  
  Hello, web world

We can access the aiohttp web app by name

  >>> import aio.web.server
  >>> web_app = aio.web.server.apps['server_name']
  >>> web_app
  <Application>

  >>> web_app['name']
  'server_name'

And we can access the jinja environment for the web app

  >>> import aiohttp_jinja2
  >>> jinja_env = aiohttp_jinja2.get_env(web_app)
  >>> jinja_env
  <jinja2.environment.Environment object ...>

We dont have any templates registered yet

  >>> jinja_env.list_templates()
  []
  
Let's clear the web apps, this will also call aio.app.clear()

  >>> aio.web.server.clear()
  >>> aio.web.server.apps
  {}

  >>> print(aio.app.config, aio.app.signals)
  None None

  
Web app modules
---------------

By default template resources are registered for any modules listed in aio:modules

  >>> config = """
  ... [aio]
  ... modules = aio.web.server
  ...          aio.web.server.tests
  ... 
  ... [server/server_name]
  ... factory = aio.web.server.factory
  ... port = 7070  
  ... """  

The aio.web.server.tests module has 2 html templates

  >>> @aiofuturetest(sleep=1)
  ... def load_server_modules(config_string):
  ...     yield from runner(['run'], config_string=config_string)  

  >>> load_server_modules(config)
  >>> web_app = aio.web.server.apps['server_name']
  >>> [x for x in aiohttp_jinja2.get_env(web_app).list_templates(extensions=["html"])]
  ['fragments/test_fragment.html', 'test_template.html']
  
  >>> aio.web.server.clear()
  
We can set the modules for all web apps in the aio/web:modules option

This will override the setting in aio:modules

  >>> config = """
  ... [aio]
  ... modules = aio.web.server
  ... 
  ... [aio/web]
  ... modules = aio.web.server.tests
  ... 
  ... [server/server_name]
  ... factory = aio.web.server.factory
  ... port = 7070  
  ... """  

  >>> load_server_modules(config)
  >>> web_app = aio.web.server.apps['server_name']
  >>> [x for x in aiohttp_jinja2.get_env(web_app).list_templates(extensions=["html"])]
  ['fragments/test_fragment.html', 'test_template.html']
  
  >>> aio.web.server.clear()

And you can set the modules in the web/server_name:modules option.

This will override the setting in both aio/web:modules and aio:modules
  
  >>> config = """
  ... [aio]
  ... modules = aio.web.server
  ...          aio.web.server.tests
  ... 
  ... [aio/web]
  ... modules = aio.web.server
  ... 
  ... [server/server_name]
  ... factory = aio.web.server.factory
  ... port = 7070  
  ... """  

  >>> load_server_modules(config)
  >>> web_app = aio.web.server.apps['server_name']
  >>> [x for x in aiohttp_jinja2.get_env(web_app).list_templates(extensions=["html"])]
  []
  
  >>> aio.web.server.clear()


Static directory
----------------

The "web/" section takes a static_url and a static_dir option for hosting static files

  >>> config_static = """
  ... [aio]
  ... log_level: ERROR
  ... modules = aio.web.server  
  ... 
  ... [server/test]
  ... factory: aio.web.server.factory
  ... port: 7070
  ... 
  ... [web/test]
  ... static_url: /static
  ... static_dir: %s
  ... """

  >>> import os
  >>> import tempfile

  >>> with tempfile.TemporaryDirectory() as tmp:
  ...     with open(os.path.join(tmp, "test.css"), 'w') as cssfile:
  ...         res = cssfile.write("body {}")
  ... 
  ...     run_web_server(
  ...         config_static % tmp,
  ...         request_page="http://localhost:7070/static/test.css")  
  body {}

And clear up...

  >>> aio.web.server.clear()
  

Routes, templates and fragments
-------------------------------

aio.web.server uses jinja2 templates under the hood

On setup aio searches the paths of modules listed in the aio:modules option for folders named "templates" and loads any templates it finds from there

  >>> config_template = """
  ... [aio]
  ... modules = aio.web.server
  ...        aio.web.server.tests
  ... log_level: ERROR
  ... 
  ... [server/example-2]
  ... factory: aio.web.server.factory
  ... port: 7070
  ... 
  ... [web/example-2/homepage]
  ... match = /
  ... route = aio.web.server.tests._example_route_handler
  ... """


Routes
~~~~~~
  
By decorating a function with @aio.web.server.route, the function is called with the request and the configuration for the route that is being handled

  >>> @aio.web.server.route("test_template.html")  
  ... def route_handler(request, config):
  ...     return {
  ...         'message': 'Hello, world'}

  >>> aio.web.server.tests._example_route_handler = route_handler
  
  >>> run_web_server(config_template)
  <html>
    <body>
      Hello, world
    </body>
  </html>

  >>> aio.web.server.clear()

Templates
~~~~~~~~~
  
A route handler can defer to other templates, for example according to the path.

The @aio.web.server.route decorator does not require a template, but in that case the decorated function must return an aiohttp.web.StreamResponse object

A route always takes 2 arguments - request and config, a template can take any arguments that it requires

While you can use an @aio.web.template as a route handler, doing so would bypass the normal logging and request handling operations

  >>> example_config = """
  ... [aio]
  ... log_level: ERROR
  ... modules = aio.web.server
  ...        aio.web.server.tests  
  ... 
  ... [server/example-3]
  ... factory: aio.web.server.factory
  ... port: 7070
  ... 
  ... [web/example-3/paths]
  ... match = /{path:.*}
  ... route = aio.web.server.tests._example_route_handler
  ... """

  >>> @aio.web.server.template("test_template.html")    
  ... def template_handler_1(request):  
  ...     return {'message': "Hello, world from template handler 1"}

  >>> @aio.web.server.template("test_template.html")  
  ... def template_handler_2(request):
  ...     return {'message': "Hello, world from template handler 2"}  

  >>> @aio.web.server.route
  ... def route_handler(request, config):
  ... 
  ...     if request.path == "/path1":
  ...         return (yield from template_handler_1(request))
  ... 
  ...     elif request.path == "/path2":
  ...         return (yield from template_handler_2(request))

  >>> aio.web.server.tests._example_route_handler = route_handler
  
  >>> run_web_server(
  ...     example_config,
  ...     request_page="http://localhost:7070/path1")  
  <html>
    <body>
      Hello, world from template handler 1
    </body>
  </html>

  >>> aio.web.server.clear()
  
  >>> run_web_server(
  ...     example_config,
  ...     request_page="http://localhost:7070/path2")  
  <html>
    <body>
      Hello, world from template handler 2
    </body>
  </html>

  >>> aio.web.server.clear()
  
Fragments
~~~~~~~~~

Both routes and templates are expected to return a full html page, or an html response object.

Fragments render a snippet of code, and are not expected to return a full page.

Fragments cannot return an html response object, but can raise an html error if required

  >>> example_config = """
  ... [aio]
  ... log_level: ERROR
  ... modules = aio.web.server
  ...        aio.web.server.tests  
  ... 
  ... [server/example-3]
  ... factory: aio.web.server.factory
  ... port: 7070
  ... 
  ... [web/example-3/paths]
  ... match = /
  ... route = aio.web.server.tests._example_route_handler
  ... """

  >>> @aio.web.server.fragment("fragments/test_fragment.html")    
  ... def fragment_handler(request, test_list):  
  ...     return {'test_list': test_list}

  >>> @aio.web.server.template("test_template.html")  
  ... def template_handler(request, test_list):
  ...     return {'message': (yield from fragment_handler(request, test_list))}  

  >>> @aio.web.server.route
  ... def route_handler(request, config):
  ... 
  ...     return (yield from template_handler(request, ["foo", "bar", "baz"]))

  >>> aio.web.server.tests._example_route_handler = route_handler
  
  >>> run_web_server(
  ...     example_config,
  ...     request_page="http://localhost:7070/")  
  <html>
    <body>
      <ul>
        <li>foo</li><li>bar</li><li>baz</li>
      </ul>
    </body>
  </html>

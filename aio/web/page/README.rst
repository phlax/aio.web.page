aio.web.page usage
------------------

aio.web.page provides templates and fragments for building web pages

Lets set up a test to run a server and request a web page

  >>> from aio.app.runner import runner    
  >>> from aio.testing import aiofuturetest
  >>> import aiohttp  

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


Templates
---------
  
An @aio.web.server.route handler can defer to other templates, for example according to the path.

  >>> example_config = """
  ... [aio]
  ... modules = aio.web.server
  ...        aio.web.server.tests  
  ... 
  ... [server/server_name]
  ... factory: aio.web.server.factory
  ... port: 7070
  ... 
  ... [web/server_name/route_name]
  ... match = /{path:.*}
  ... route = aio.web.page.tests._example_route_handler
  ... """

Lets create a couple of template handlers

  >>> import aio.web.page

  >>> @aio.web.page.template("test_template.html")    
  ... def template_handler_1(request):  
  ...     return {
  ...         'message': "Hello, world from template handler 1"}

Template handlers dont have to specify a template, but they must return a response object if they dont
  
  >>> @aio.web.page.template
  ... def template_handler_2(request):
  ...     return aiohttp.web.Response(
  ...         body=b"Hello, world from template handler 2")


And lets set up a route handler which will defer to a template according to the route

  >>> import aio.web.server

  >>> @aio.web.server.route
  ... def route_handler(request, config):
  ... 
  ...     if request.path == "/path1":
  ...         return (yield from template_handler_1(request))
  ... 
  ...     elif request.path == "/path2":
  ...         return (yield from template_handler_2(request))
  ... 
  ...     raise aiohttp.web.HTTPNotFound

And make it importable
  
  >>> import aio.web.page.tests
  >>> aio.web.page.tests._example_route_handler = route_handler

Calling the server at /path1 we get the templated handler
  
  >>> run_web_server(
  ...     example_config,
  ...     request_page="http://localhost:7070/path1")  
  <html>
    <body>
      Hello, world from template handler 1
    </body>
  </html>

  >>> aio.web.server.clear()

And calling on /path2 we get the response from the handler without a template
  
  >>> run_web_server(
  ...     example_config,
  ...     request_page="http://localhost:7070/path2")  
  Hello, world from template handler 2
    
  >>> aio.web.server.clear()


Fragments
---------

Fragments render a snippet of html for embedding in other templates.

Fragments must always specify a template

  >>> @aio.web.page.fragment("fragments/test_fragment.html")    
  ... def fragment_handler(request, test_list):  
  ...     return {'test_list': test_list}

And fragment handlers should always return a context dictionary.
  
Both templates and fragments can take arbitrary arguments
  
  >>> @aio.web.page.template("test_template.html")  
  ... def template_handler(request, test_list):
  ...     return {'message': (yield from fragment_handler(request, test_list))}  

Whereas a route always receives (request, config)
  
  >>> @aio.web.server.route
  ... def route_handler(request, config):
  ... 
  ...     return (yield from template_handler(request, ["foo", "bar", "baz"]))

  >>> aio.web.page.tests._example_route_handler = route_handler
  
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

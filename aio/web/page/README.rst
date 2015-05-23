aio.web.server usage
--------------------

Lets set up a test to run the server and request a web page

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
  ... log_level: ERROR
  ... modules = aio.web.server
  ...        aio.web.server.tests  
  ... 
  ... [server/server_name]
  ... factory: aio.web.server.factory
  ... port: 7070
  ... 
  ... [web/server_name/route_name]
  ... match = /{path:.*}
  ... route = aio.web.server.tests._example_route_handler
  ... """

Lets create a couple of template handlers

  >>> import aio.web.page

  >>> @aio.web.page.template("test_template.html")    
  ... def template_handler_1(request):  
  ...     return {'message': "Hello, world from template handler 1"}

  >>> @aio.web.page.template("test_template.html")  
  ... def template_handler_2(request):
  ...     return {'message': "Hello, world from template handler 2"}  


And lets set up a aio.web.server.route

  >>> import aio.web.server

  >>> @aio.web.server.route
  ... def route_handler(request, config):
  ... 
  ...     if request.path == "/path1":
  ...         return (yield from template_handler_1(request))
  ... 
  ...     elif request.path == "/path2":
  ...         return (yield from template_handler_2(request))

  >>> import aio.web.server.tests

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
---------

Both routes and templates are expected to return a full html page, or an html response object.

Fragments render a snippet of code, and are not expected to return a full page.

Fragment handlers should return a context or dictionary and should not return an html response object.

Fragments can raise an html error if relevant, and is then up to the template or route to handle the exception.

  >>> example_config = """
  ... [aio]
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

  >>> @aio.web.page.fragment("fragments/test_fragment.html")    
  ... def fragment_handler(request, test_list):  
  ...     return {'test_list': test_list}

  >>> @aio.web.page.template("test_template.html")  
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

aio.web.page usage
------------------

aio.web.page provides templates and fragments for building web pages

Lets set up a test to run a server and request a web page

>>> from aio.app.runner import runner    
>>> import aio.testing
>>> import aiohttp  

>>> @aio.testing.run_forever(sleep=1)
... def run_web_server(config, request_page="http://localhost:7070"):
...     yield from runner(['run'], config_string=config)
... 
...     def call_web_server():
...         result = yield from (
...             yield from aiohttp.request(
...                "GET", request_page)).read()
...         aio.web.server.clear()
... 
...         print(result.decode())
... 
...     return call_web_server


Templates
---------
  
An @aio.web.server.route handler can defer to other templates, for example according to the matched path.

>>> example_config = """
... [aio]
... log_level = CRITICAL
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

Template handlers can return a response object, in which case the template is not rendered
  
>>> @aio.web.page.template("test_template.html")
... def template_handler_2(request):
...     return aiohttp.web.Response(
...         body=b"Hello, world from template handler 2")


And lets set up a route handler which will defer to a template accordingly

>>> import aio.web.server

>>> @aio.web.server.route
... def route_handler(request, config):
...     path = request.match_info['path']
... 
...     if path == "path1":
...         return (yield from template_handler_1(request))
... 
...     elif path == "path2":
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

And calling on /path2 we get the response without the template
  
>>> run_web_server(
...     example_config,
...     request_page="http://localhost:7070/path2")  
Hello, world from template handler 2


Templates must always specify a template, even if they dont use it

>>> try:
...     @aio.web.page.template
...     def template_handler(request, test_list):  
...         return {'test_list': test_list}
... except Exception as e:
...     print(repr(e))
TypeError('Template decorator must specify template: <function template_handler ...>',)

Templates can take arbitrary arguments

>>> @aio.web.page.template("test_template.html")    
... def template_handler(request, foo, bar):  
...     return {
...         'message': "Hello, world with %s and %s" % (foo, bar)}

>>> @aio.web.server.route
... def route_handler(request, config):
...     return (yield from(template_handler(request, "spam", "tuesday")))
>>> aio.web.page.tests._example_route_handler = route_handler

>>> run_web_server(example_config)
<html>
  <body>
    Hello, world with spam and tuesday
  </body>
</html>

The first argument to a template should always be a request object

>>> @aio.web.page.template("test_template.html")    
... def template_handler(foo, bar):  
...     return {
...         'message': "Hello, world with %s and %s" % (foo, bar)}

>>> @aio.web.server.route
... def route_handler(request, config):
...     try:
...         return (yield from(template_handler("spam", "tuesday")))
...     except TypeError as e:
...         return aiohttp.web.Response(body=str(e).encode())
>>> aio.web.page.tests._example_route_handler = route_handler

>>> run_web_server(example_config)
Template handler should be called with a request object, got: spam


Fragments
---------

Fragments render a snippet of html for embedding in other templates.

Fragments can specify a template and return a context object to render it with

A fragment can take an arbitrary number of arguments

>>> @aio.web.page.fragment("fragments/test_fragment.html")
... def fragment_handler(request, foo, bar):
...     return {"test_list": [foo, bar]}

>>> @aio.web.page.template("test_template.html")    
... def template_handler(request):
...     return {'message': (yield from fragment_handler(request, "eggs", "thursday"))}

>>> @aio.web.server.route
... def route_handler(request, config):
...     return (yield from(template_handler(request)))
>>> aio.web.page.tests._example_route_handler = route_handler

>>> run_web_server(example_config)
<html>
  <body>
    <ul>
      <li>eggs</li><li>thursday</li>
    </ul>
  </body>
</html>

The first argument to a fragment should always be an aiohttp.web.Request object

>>> @aio.web.page.fragment("fragments/test_fragment.html")
... def fragment_handler(foo, bar):
...     return {"test_list": [foo, bar]}

>>> @aio.web.page.template("test_template.html")    
... def template_handler(request):
...     try:
...         message = (yield from(fragment_handler("eggs", "thursday")))
...     except Exception as e:
...         message = repr(e)
...     return {'message': message}

>>> @aio.web.server.route
... def route_handler(request, config):
...     return (yield from(template_handler(request)))
>>> aio.web.page.tests._example_route_handler = route_handler

>>> run_web_server(example_config)
<html>
  <body>
    TypeError('Fragment handler should be called with a request object, got: eggs',)
  </body>
</html>


Fragments do not need to specify a template

>>> @aio.web.page.fragment
... def fragment_handler(request):
...     return "Hello from fragment"

>>> @aio.web.page.template("test_template.html")  
... def template_handler(request):
...     return {'message': (yield from fragment_handler(request))}  

>>> @aio.web.server.route
... def route_handler(request, config):
...     return (yield from(template_handler(request)))
>>> aio.web.page.tests._example_route_handler = route_handler

>>> run_web_server(example_config)
<html>
  <body>
    Hello from fragment
  </body>
</html>

If a fragment doesnt specify a template, it must return a string

>>> @aio.web.page.fragment
... def fragment_handler(request):
...     return {"foo": "bar"}

>>> @aio.web.page.template("test_template.html")  
... def template_handler(request):
...     try:
...         fragment = yield from fragment_handler(request)
...     except Exception as e:
...         fragment = repr(e)
...     return {'message': fragment}

>>> @aio.web.server.route
... def route_handler(request, config):
...     return (yield from(template_handler(request)))
>>> aio.web.page.tests._example_route_handler = route_handler

>>> run_web_server(example_config)
<html>
  <body>
    TypeError('Fragment handler (<function fragment_handler at ...>) should specify a template or return a string',)
  </body>
</html>

Fragments should only return strings or context dictionaries, and should not return an aiohttp.web.Response object.

>>> @aio.web.page.fragment("fragments/test_fragment.html")
... def fragment_handler(request):
...     return aiohttp.web.Response(body=b"Fragments should not return Response objects")

>>> @aio.web.page.template("test_template.html")  
... def template_handler(request):
...     try:
...         fragment = yield from fragment_handler(request)
...     except Exception as e:
...         fragment = repr(e)
...     return {'message': fragment}

>>> @aio.web.server.route
... def route_handler(request, config):
...     return (yield from(template_handler(request)))
>>> aio.web.page.tests._example_route_handler = route_handler

>>> run_web_server(example_config)
<html>
  <body>
    TypeError('Fragment handler (<function fragment_handler at ...>) should return a string or context dictionary',)
  </body>
</html>




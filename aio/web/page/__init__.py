import asyncio
import functools

import aiohttp
import aiohttp_jinja2

import logging
log = logging.getLogger("aio.web")
apps = {}


def template(*la, **kwa):
    """
    calls handler
    - hander can return a response object or context
    - if response object, response is returned
    - else the the template is rendered
    """
    app_key = kwa.get("app_key", aiohttp_jinja2.APP_KEY)
    encoding = kwa.get("encoding", 'utf-8')
    status = kwa.get("status", 200)

    try:
        template_name = la[0]
        assert(isinstance(template_name, str))
    except (IndexError, AssertionError):
        raise TypeError(
            "Template decorator must specify template: %s" % la[0])

    def wrapper(func):

        @asyncio.coroutine
        @functools.wraps(func)
        def wrapped(*la, **kwa):
            try:
                request = la[0]
                assert(isinstance(
                    request, aiohttp.web.Request))
            except (IndexError, AssertionError):
                raise TypeError(
                    "Template handler (%s) should be called with " % func
                    + "a request object, got: %s %s" % (type(la[0]), la[0]))

            if asyncio.iscoroutinefunction(func):
                coro = func
            else:
                coro = asyncio.coroutine(func)

            try:
                context = yield from coro(*la)
            except Exception as e:
                import traceback
                traceback.print_exc()
                log.error("Error calling template handler: %s" % e)
                raise e

            if isinstance(context, aiohttp.web.StreamResponse):
                return context

            try:
                response = aiohttp_jinja2.render_template(
                    template_name, request, context,
                    app_key=app_key,
                    encoding=encoding)
                response.set_status(status)
            except Exception as e:
                import traceback
                traceback.print_exc()
                log.error("Error calling template (%s): %s" % (
                    template_name, e))
                raise e
            return response
        return wrapped
    if len(la) == 1 and callable(la[0]):
        return wrapper(la[0])
    return wrapper


def fragment(*la, **kwa):
    app_key = kwa.get("app_key", aiohttp_jinja2.APP_KEY)

    template_name = None
    if isinstance(la[0], str):
        template_name = la[0]

    def wrapper(func):

        @asyncio.coroutine
        @functools.wraps(func)
        def wrapped(*la, **kwa):
            try:
                request = la[0]
                assert(isinstance(
                    request, aiohttp.web.Request))
            except (IndexError, AssertionError):
                raise TypeError(
                    "Fragment handler (%s) should be called with " % func
                    + "a request object, got: %s %s" % (type(la[0]), la[0]))

            if asyncio.iscoroutinefunction(func):
                coro = func
            else:
                coro = asyncio.coroutine(func)

            try:
                context = yield from coro(*la)
            except Exception as e:
                import traceback
                traceback.print_exc()
                log.error("Error calling fragment handler: %s" % e)
                raise e

            if isinstance(context, str):
                return context

            if not isinstance(context, dict):
                error_message = (
                    "Fragment handler (%s) should return a string " % func
                    + "or context dictionary, got: %s %s" % (
                        type(context), context))
                log.error(error_message)
                raise TypeError(error_message)

            if not template_name:
                error_message = (
                    "Fragment handler (%s) should specify a template" % func
                    + " or return a string")
                log.error(error_message)
                raise TypeError(error_message)

            try:
                response = aiohttp_jinja2.render_string(
                    template_name, request, context,
                    app_key=app_key)
            except Exception as e:
                import traceback
                traceback.print_exc()
                log.error("Error calling fragment (%s): %s" % (
                    template_name, e))
                raise e
            return response
        return wrapped
    if len(la) == 1 and callable(la[0]):
        return wrapper(la[0])
    return wrapper

# this needs to be done after fragment is defined
from aio.web.page import fragments
fragments = fragments



class View(object):

    def __init__(self, request, template_name=None,
                 app_key=None, encoding=None, status=None,
                 context=None):
        self.request = request
        self._template = template_name
        self._app_key = app_key
        self._encoding = encoding
        self._status = status
        self._context = context or {}
        self._responder = None
        
    def get_template(self):
        return self._template

    def set_template(self, template_name):
        self._template = template_name

    def get_encoding(self):
        return self._encoding or "utf-8"

    def set_encoding(self, encoding):
        self._encoding = encoding

    def get_status(self):
        return self._status or 200

    def get_app_key(self):
        return self._app_key or aiohttp_jinja2.APP_KEY

    def get_context(self):
        return self._context

    def set_context(self, context):
        self._context = context

    def update_context(self, context):
        self._context.update(context)

    def get_responder(self):
        return self._responder or aiohttp_jinja2.render_template

    def get_response_args(self):
        return (
            self.get_template(),
            self.request,
            self.get_context())

    def get_response_kwargs(self):
        return dict(
            app_key=self.get_app_key(),
            encoding=self.get_encoding())

    @asyncio.coroutine
    def handle_request(self, request):
        pass

    @asyncio.coroutine    
    def handle_success(self):
        try:
            response = self.get_responder(
                *self.get_responder_args(),
                **self.get_responder_kwargs())    
            response.set_status(self.get_status())
        except Exception as e:
            return self.handle_error(e)
        return response

    @asyncio.coroutine
    def handle_error(self, e):
        import traceback
        traceback.print_exc()
        log.error("Error calling view (%s): %s" % (
            self, e))
        raise e
        
    @asyncio.coroutine
    def respond(self, context=None):
        self.update_context(context or {})
        try:
            yield from self.handle_request(self.request)            
            return (yield from self.handle_success())
        except Exception as e:
            return (yield from self.handle_error(e))

    
class FormView(View):

    def get_redirect_url(self):
        return self._redirect_url

    def get_success_template(self):
        return self._success_template
    
    def get_form_class(self):
        return self._form_class

    def set_form_class(self, form_class):
        self._form_class = form_class
    
    def get_form(self):
        return self.get_form_class(
            *self.get_form_args(),
            **self.get_form_kwargs())

    def get_form_args(self):
        return self.reqest.post,

    def get_form_kwargs(self):
        return {}
        
    @asyncio.coroutine
    def handle_request(self, request):
        if request.post:
            try:
                yield from self.get_form().post(
                    *self.get_form_args(),
                    **self.get_form_kwargs())
            except Exception as e:
                yield from self.handle_error(e)

    @asyncio.coroutine                
    def handle_form_success(self):
        if self.get_redirect_url():
            return aio.http.server.redirect(
                self.get_redirect_url())
        elif self.get_success_template():
            self.set_template(
                self.get_success_template())
        try:
            response = self.get_responder(
                *self.get_responder_args(),
                **self.get_responder_kwargs())    
            response.set_status(self.get_status())
        except Exception as e:
            return self.handle_error(e)
        return response
        
    @asyncio.coroutine    
    def handle_form_failure(self):
        # set any errors on the context here...
        try:
            response = self.get_responder(
                *self.get_responder_args(),
                **self.get_responder_kwargs())    
            response.set_status(self.get_status())
        except Exception as e:
            return self.handle_error(e)
        return response

    @asyncio.coroutine
    def handle_success(self):
        if self.get_form().errors:
            return (yield from self.handle_form_failure())
        else:
            return (yield from self.handle_form_success())
        

def view(*la, **kwa):
    """
    calls handler
    - hander can return a response object or context
    - if response object, response is returned
    - else the the template is rendered
    """
    app_key = kwa.get("app_key", aiohttp_jinja2.APP_KEY)
    encoding = kwa.get("encoding", 'utf-8')
    status = kwa.get("status", 200)

    try:
        template_name = kwa.get("template_name", la[0])
        assert(isinstance(template_name, str))
    except (IndexError, AssertionError):
        raise TypeError(
            "Template decorator must specify template: %s" % la[0])

    view_class = kwa.get('view', View)

    def wrapper(func):

        @asyncio.coroutine
        @functools.wraps(func)
        def wrapped(*la, **kwa):
            try:
                request = la[0]
                assert(isinstance(
                    request, aiohttp.web.Request))
            except (IndexError, AssertionError):
                raise TypeError(
                    "Template handler (%s) should be called with " % func
                    + "a request object, got: %s %s" % (type(la[0]), la[0]))

            if asyncio.iscoroutinefunction(func):
                coro = func
            else:
                coro = asyncio.coroutine(func)

            try:
                view = view_class(la[0], template_name=template_name)
                return (yield from coro(view, *la[1:]))
            except Exception as e:
                import traceback
                traceback.print_exc()
                log.error("Error calling template handler: %s" % e)
                raise e

            return view

        return wrapped
    if len(la) == 1 and callable(la[0]):
        return wrapper(la[0])
    return wrapper

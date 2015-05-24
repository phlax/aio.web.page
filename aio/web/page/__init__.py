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

from aio.web.page import fragments
fragments = fragments

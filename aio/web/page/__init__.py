import os
import asyncio
import functools
import mimetypes

from zope.dottedname.resolve import resolve
import aiohttp
import aiohttp_jinja2

import aio.app
import aio.http.server
import aio.web.server
from aio.core.exceptions import MissingConfiguration

import logging
log = logging.getLogger("aio.web")
apps = {}


def template(*la, **kwa):
    """
    calls handler
    - hander can return a response object or context
    - if context, context is returned
    - else the the template is rendered
    """
    app_key = kwa.get("app_key", aiohttp_jinja2.APP_KEY)
    encoding = kwa.get("encoding", 'utf-8')
    status = kwa.get("status", 200)

    if len(la) == 1 and not callable(la[0]):
        template_name = la[0]
    else:
        template_name = None

    def wrapper(func):

        @asyncio.coroutine
        @functools.wraps(func)
        def wrapped(*la, **kwa):
            request = la[0]

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

    if len(la) == 1 and not callable(la[0]):
        template_name = la[0]
    else:
        template_name = None

    def wrapper(func):

        @asyncio.coroutine
        @functools.wraps(func)
        def wrapped(*la, **kwa):
            request = la[0]

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

            if not template_name:
                error_message = (
                    "Fragment handler (%s) should provide a template" % func
                    + " or return a string")
                log.error(error_message)
                raise Exception(error_message)

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


def filestream(request, filepath):
    resp = aiohttp.web.StreamResponse()
    limit = aiohttp.web_urldispatcher.StaticRoute.limit
    ct, encoding = mimetypes.guess_type(
        os.path.basename(filepath))
    if not ct:
        ct = 'application/octet-stream'
    resp.content_type = ct
    if encoding:
        resp.headers['content-encoding'] = encoding

    file_size = os.stat(filepath).st_size
    single_chunk = file_size < limit

    if single_chunk:
        resp.content_length = file_size
    resp.start(request)

    with open(filepath, 'rb') as f:
        chunk = f.read(limit)
        if single_chunk:
            resp.write(chunk)
        else:
            while chunk:
                resp.write(chunk)
                chunk = f.read(limit)
    return resp

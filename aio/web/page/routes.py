import aiohttp

import aio.web


@aio.web.server.route
def hello_world_route(request, config):
    return aiohttp.web.Response(body=b"Hello, web world")

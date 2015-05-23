from aio.web.page import fragment


@fragment('header.html')
def header(request, config, title=None):
    return {'header': title or (config and config.name or '')}


@fragment('footer.html')
def footer(request, config=None):
    return {}

from aio.app.testing import AioAppTestCase

import aio.web.server


class AioWebAppTestCase(AioAppTestCase):

    def tearDown(self):
        super(AioWebAppTestCase, self).tearDown()
        aio.web.server.clear()

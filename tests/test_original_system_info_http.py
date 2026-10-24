# -*- coding: utf-8 -*-
"""Stock 1.3.2 API/CherryPy regression test; loopback and synthetic JWT key only."""
import httplib
import json
import socket
import time
import unittest

import cherrypy
from base.Plugin import PluginContext
from api import ApiManager
from board import Board
from telldus import DeviceApiManager
from web.base.Server import RequestHandler


class SystemInfoHttp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        listener = socket.socket()
        listener.bind(('127.0.0.1', 0))
        cls.port = listener.getsockname()[1]
        listener.close()
        context = PluginContext()
        cls.api = ApiManager(context)
        cls.api.tokenKey = 'synthetic-test-key-for-loopback-only'
        DeviceApiManager.DeviceApiManager(context)
        Board.product = staticmethod(lambda: 'synthetic-znet')
        Board.firmwareVersion = staticmethod(lambda: '1.3.2-test')
        cherrypy.config.update({'server.socket_host': '127.0.0.1',
                                'server.socket_port': cls.port,
                                'tools.sessions.on': True,
                                'log.screen': False})
        cherrypy.tree.mount(RequestHandler(context), '')
        cherrypy.engine.start()

    @classmethod
    def tearDownClass(cls):
        cherrypy.engine.exit()

    def get(self, authorization=None, method='GET'):
        conn = httplib.HTTPConnection('127.0.0.1', self.port, timeout=5)
        headers = {}
        if authorization is not None:
            headers['Authorization'] = authorization
        conn.request(method, '/api/system/info', headers=headers)
        response = conn.getresponse()
        result = (response.status, json.loads(response.read()))
        conn.close()
        return result

    def token(self, exp):
        return self.api._ApiManager__generateToken(
            {}, {'aud': 'synthetic-client', 'exp': exp})

    def test_no_authorization_header(self):
        status, body = self.get()
        self.assertEqual(status, 401)
        self.assertEqual(body['error'], 'No token was found in the request')

    def test_empty_authorization_header(self):
        status, body = self.get('')
        self.assertEqual(status, 401)
        self.assertEqual(body['error'], 'The autorization token must be supplied as a bearer token')

    def test_wrong_bearer_format(self):
        status, body = self.get('Basic synthetic')
        self.assertEqual(status, 401)
        self.assertEqual(body['error'], 'The autorization token must be supplied as a bearer token')

    def test_invalid_jwt(self):
        status, body = self.get('Bearer not-a-jwt')
        self.assertEqual(status, 401)
        self.assertIn('error', body)

    def test_expired_jwt(self):
        status, body = self.get('Bearer ' + self.token(int(time.time()) - 60))
        self.assertEqual(status, 401)
        self.assertEqual(body['error'], 'The token has expired')

    def test_valid_jwt(self):
        status, body = self.get('Bearer ' + self.token(int(time.time()) + 300))
        self.assertEqual(status, 200)
        self.assertIn('product', body)
        self.assertIn('version', body)
        self.assertIn('time', body)


if __name__ == '__main__':
    unittest.main(verbosity=2)

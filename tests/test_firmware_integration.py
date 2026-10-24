# -*- coding: utf-8 -*-
"""QEMU MIPS Python 2.7 integration with original firmware modules.
Only synthetic settings, credentials and request objects. No listener/socket.
"""
import base64
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
import unittest

from base.Plugin import PluginContext
from api import ApiManager
from telldus import DeviceApiManager
from localowner import LocalOwnerAuth
from tellduslive.web import WebRequestHandler as LiveProvider

api_module = sys.modules[ApiManager.__module__]
owner_module = sys.modules[LocalOwnerAuth.__module__]
device_api_module = DeviceApiManager

class FakeSettings(dict):
    sections = {}
    def __init__(self, section):
        super(FakeSettings, self).__init__()
        self.section = section
    def get(self, key, default=None):
        return self.sections.get(self.section, {}).get(key, default)
    def __setitem__(self, key, value):
        self.sections.setdefault(self.section, {})[key] = value

class FakeDevice(object):
    def id(self): return 12
    def name(self): return 'Synthetic RF433 light'
    def isDevice(self): return True
    def isSensor(self): return False
    def state(self): return (1, None)
    def methods(self): return 3
class FakeSensor(object):
    def id(self): return 17
    def name(self): return 'Synthetic temperature'
    def isDevice(self): return False
    def isSensor(self): return True
    def protocol(self): return 'synthetic'
    def model(self): return 'offline'
    def battery(self): return None
    def sensorValues(self): return {}
class FakeDeviceManager(object):
    def __init__(self, context): pass
    def retrieveDevices(self): return [FakeDevice(), FakeSensor()]
class FakeCherryPyRequest(object):
    scheme = 'https'
    path_info = '/localowner/login'

class FakeSession(object):
    def __init__(self):
        self.regenerations = 0
    def regenerate(self):
        self.regenerations += 1

class FakeCherryPy(object):
    request = FakeCherryPyRequest()
    session = FakeSession()

class FakeRequest(object):
    def __init__(self, method='GET', form=None, session=None, headers=None):
        self._method = method
        self.form = form or {}
        self.store = session if session is not None else {}
        self.headers = headers or {}
    def method(self):
        return self._method
    def post(self, key, default=None):
        return self.form.get(key, default)
    def params(self):
        return self.form
    def session(self, key, default=None):
        return self.store.get(key, default)
    def setSession(self, key, value):
        self.store[key] = value
    def header(self, key):
        return self.headers.get(key)
    def base(self):
        return 'https://isolated.test'

class Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix='local-owner-', dir=os.path.dirname(__file__))
        cls.owner_path = os.path.join(cls.tmp, 'owner.json')
        salt = b'synthetic-salt-16'
        verifier = hashlib.pbkdf2_hmac('sha256', 'synthetic-password', salt, 200000)
        with open(cls.owner_path, 'w') as stream:
            json.dump({'algorithm':'pbkdf2-sha256', 'iterations':200000,
                       'salt':base64.b64encode(salt),
                       'verifier':base64.b64encode(verifier)}, stream)
        os.chmod(cls.owner_path, 0600)
        owner_module.OWNER_FILE = cls.owner_path
        owner_module.cherrypy = FakeCherryPy()
        api_module.Settings = FakeSettings
        device_api_module.DeviceManager = FakeDeviceManager
        api_module.Board.secret = staticmethod(lambda:'synthetic-machine')
        api_module.Board.product = staticmethod(lambda:'synthetic-znet')
        api_module.Board.firmwareVersion = staticmethod(lambda:'1.3.2-test')
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)
    def setUp(self):
        FakeSettings.sections = {}
        self.ctx = PluginContext()
        self.api = ApiManager(self.ctx)
        self.owner = LocalOwnerAuth(self.ctx)
        self.session = {}
        owner_module.cherrypy.request.scheme = 'https'
        owner_module.cherrypy.request.path_info = '/localowner/login'
    def pending(self):
        response = self.api.handleRequest('api','token',{},FakeRequest('PUT', {'app':'synthetic-client'}))
        self.assertEqual(response.statusCode,200)
        return json.loads(response.data)['token']
    def login(self):
        self.owner.handleRequest('localowner','login',{},FakeRequest('GET',session=self.session))
        token = self.session['localowner_login_csrf']
        response = self.owner.handleRequest('localowner','login',{},
            FakeRequest('POST',{'csrf':token,'password':'synthetic-password'},self.session))
        self.assertEqual(response.statusCode,200)
        self.assertTrue(self.session['localowner_authenticated'])
    def approve(self, pending, renew=True):
        owner_module.cherrypy.request.path_info = '/localowner/approve'
        self.owner.handleRequest('localowner','approve',{'token':pending},
                                 FakeRequest('GET',session=self.session))
        csrf = self.session['localowner_approve_csrf']
        response = self.owner.handleRequest('localowner','approve',{'token':pending},
                    FakeRequest('POST',{'csrf':csrf,'ttl':'1440','extend':'1' if renew else ''},self.session))
        self.assertEqual(response.statusCode,200)
    def token(self, req):
        response = self.api.handleRequest('api','token',{'token':req},FakeRequest('GET'))
        self.assertEqual(response.statusCode,200)
        return json.loads(response.data)['token']
    def test_original_api_issue_validate_refresh_and_route(self):
        req = self.pending()
        self.login()
        self.approve(req,True)
        jwt = self.token(req)
        header = {'Authorization':'Bearer '+jwt}
        response = self.api.handleRequest('api','system/info',{},FakeRequest('GET',headers=header))
        self.assertEqual(response.statusCode,200)
        self.assertEqual(json.loads(response.data)['product'],'synthetic-znet')
        response = self.api.handleRequest('api','refreshToken',{},FakeRequest('GET',headers=header))
        self.assertEqual(response.statusCode,200)
        newer = json.loads(response.data)['token']
        self.assertNotEqual(newer,'')
        self.assertEqual(self.api.handleRequest('api','system/info',{},FakeRequest('GET',headers={'Authorization':'Bearer bad'})).statusCode,401)
    def test_original_device_and_sensor_list_routes(self):
        req=self.pending()
        self.login()
        self.approve(req)
        jwt=self.token(req)
        headers={'Authorization':'Bearer '+jwt}
        dev=self.api.handleRequest('api','devices/list',{},FakeRequest('GET',headers=headers))
        sen=self.api.handleRequest('api','sensors/list',{},FakeRequest('GET',headers=headers))
        self.assertEqual(json.loads(dev.data)['device'][0]['name'],'Synthetic RF433 light')
        self.assertEqual(json.loads(sen.data)['sensor'][0]['name'],'Synthetic temperature')
    def test_owner_denials_csrf_and_secure_transport(self):
        req = self.pending()
        self.owner.handleRequest('localowner','login',{},FakeRequest('GET',session=self.session))
        bad = self.owner.handleRequest('localowner','login',{},
            FakeRequest('POST',{'csrf':self.session['localowner_login_csrf'],'password':'wrong'},self.session))
        self.assertEqual(bad.statusCode,403)
        self.login()
        owner_module.cherrypy.request.path_info = '/localowner/approve'
        self.owner.handleRequest('localowner','approve',{'token':req},FakeRequest('GET',session=self.session))
        bad = self.owner.handleRequest('localowner','approve',{'token':req},
            FakeRequest('POST',{'csrf':'wrong','ttl':'1440'},self.session))
        self.assertEqual(bad.statusCode,403)
        self.assertFalse(self.api.tokens[req]['authorized'])
        owner_module.cherrypy.request.scheme = 'http'
        self.assertFalse(self.owner.isUrlAuthorized(FakeRequest(session=self.session)))
        self.assertEqual(self.owner.handleRequest('localowner','approve',{'token':req},
            FakeRequest('GET',session=self.session)).statusCode,403)
    def test_login_rate_limit(self):
        for _ in range(5):
            self.owner._record_login('unknown', False)
        self.owner.handleRequest('localowner','login',{},FakeRequest('GET',session=self.session))
        response = self.owner.handleRequest('localowner','login',{},
            FakeRequest('POST',{'csrf':self.session['localowner_login_csrf'],
                                'password':'synthetic-password'},self.session))
        self.assertEqual(response.statusCode,429)
        self.assertFalse(self.session.get('localowner_authenticated',False))
    def test_original_live_provider_remains_available(self):
        live = LiveProvider(self.ctx)
        self.assertEqual(live.loginProvider()['url'], '/tellduslive/login')
        self.assertFalse(live.isUrlAuthorized(FakeRequest(session=self.session)))
        self.session['loggedIn'] = True
        self.assertTrue(live.isUrlAuthorized(FakeRequest(session=self.session)))
    def test_stock_approval_blocked_for_local_session(self):
        self.login()
        owner_module.cherrypy.request.path_info = '/api/authorize'
        self.assertFalse(self.owner.isUrlAuthorized(FakeRequest('POST',session=self.session)))
    def test_session_expiry_and_logout(self):
        self.login()
        owner_module.cherrypy.request.path_info = '/localowner/approve'
        self.session['localowner_until'] = time.time()-1
        self.assertFalse(self.owner.isUrlAuthorized(FakeRequest(session=self.session)))
        self.session['localowner_until'] = time.time()+1800
        req = self.pending()
        self.owner.handleRequest('localowner','logout',{},FakeRequest('GET',session=self.session))
        csrf = self.session['localowner_logout_csrf']
        self.assertEqual(self.owner.handleRequest('localowner','logout',{},
            FakeRequest('POST',{'csrf':csrf},self.session)).statusCode,200)
        self.assertFalse(self.owner.isUrlAuthorized(FakeRequest(session=self.session)))
    def test_expired_jwt_and_nonrenewable(self):
        req = self.pending()
        self.login()
        self.approve(req,False)
        jwt = self.token(req)
        token_header = {'Authorization':'Bearer '+jwt}
        response = self.api.handleRequest('api','refreshToken',{},FakeRequest('GET',headers=token_header))
        self.assertEqual(response.statusCode,403)
        old_time = api_module.time
        class FutureTime(object):
            @staticmethod
            def time():
                return time.time()+90000
        api_module.time = FutureTime()
        try:
            response = self.api.handleRequest('api','system/info',{},FakeRequest('GET',headers=token_header))
            self.assertEqual(response.statusCode,401)
        finally:
            api_module.time = old_time

if __name__ == '__main__':
    unittest.main(verbosity=2)

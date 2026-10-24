# -*- coding: utf-8 -*-
import time
import sys
import os
from base import Application
from api import ApiManager
from telldus import DeviceApiManager
from localowner import LocalOwnerAuth, LocalHttpsServer

if os.environ.get('LOCALOWNER_LOCAL_ONLY') != '1':
    from tellduslive.web import WebRequestHandler as LiveProvider
else:
    LiveProvider = None

class FakeSettings(dict):
    sections = {}
    def __init__(self, section):
        self.section = section
    def get(self, key, default=None):
        return self.sections.get(self.section, {}).get(key, default)
    def __setitem__(self, key, value):
        self.sections.setdefault(self.section, {})[key] = value

class FakeDevice(object):
    def id(self): return 12
    def name(self): return 'Synthetic switch'
    def isDevice(self): return True
    def isSensor(self): return False
    def state(self): return (1, None)
    def methods(self): return 3
    def command(self, method, value, origin=None): return True
class FakeSensor(object):
    def id(self): return 17
    def name(self): return 'Synthetic sensor'
    def isDevice(self): return False
    def isSensor(self): return True
    def protocol(self): return 'synthetic'
    def model(self): return 'offline'
    def battery(self): return None
    def sensorValues(self): return {}
class FakeDeviceManager(object):
    def __init__(self, context): pass
    def retrieveDevices(self): return [FakeDevice(), FakeSensor()]
    def device(self, device_id):
        return FakeDevice() if int(device_id)==12 else None

DeviceApiManager.DeviceManager = FakeDeviceManager
api_module = sys.modules[ApiManager.__module__]
api_module.Settings = FakeSettings
api_module.Board.secret = staticmethod(lambda: 'synthetic-machine')
api_module.Board.product = staticmethod(lambda: 'synthetic-znet')
api_module.Board.firmwareVersion = staticmethod(lambda: '1.3.2-test')
app = Application(run=False)
ctx = app.pluginContext
ApiManager(ctx)
if LiveProvider is not None:
    LiveProvider(ctx)
LocalOwnerAuth(ctx)
LocalHttpsServer(ctx)
while True:
    time.sleep(1)

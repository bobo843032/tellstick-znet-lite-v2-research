# -*- coding: utf-8 -*-
"""Safe stock-bytecode parser/listener tests; no network or serial hardware."""
import importlib
import unittest
from tellduslive.base import LiveMessage

module = importlib.import_module('productiontest.Server')
OriginalServer = module.Server

class FakeSocket(object):
    def __init__(self): self.sent = []
    def sendto(self, payload, address): self.sent.append((payload, address))

class FakeAdapter(object):
    def __init__(self): self.queued = []
    def queue(self, item): self.queued.append(item)

class FakeRF(object):
    def __init__(self): self.dev = FakeAdapter()

class FakeController(object):
    def version(self): return 'synthetic-controller'

class FakeZWave(object):
    controller = FakeController()

class OriginalUdp42314(unittest.TestCase):
    def setUp(self):
        self.server = object.__new__(OriginalServer)
        self.server.listener = None
        self.server.clientAddress = None
        self.server.zwave = None
        self.original_server = module.Server
        module.Server = lambda context: self.server
        module.CommandHandler.context = object()
        module.CommandHandler.rf433 = FakeRF()

    def tearDown(self):
        module.Server = self.original_server

    def handle(self, payload, address=('127.0.0.1', 10001)):
        sock = FakeSocket()
        module.CommandHandler((payload, sock), address, object())
        return sock

    def test_original_parser_roundtrip_inert_message(self):
        msg = LiveMessage('notice')
        msg.append({'name':'synthetic', 'count':2})
        parsed = LiveMessage.fromByteArray(msg.toByteArray())
        self.assertEqual(parsed.name(), 'notice')
        self.assertEqual(parsed.argument(0).toNative()['count'], 2)

    def test_malformed_parser_is_not_strict(self):
        self.assertEqual(LiveMessage.fromByteArray('iZs').name(), '')
        # Declared length exceeds supplied bytes; original parser still accepts it.
        self.assertEqual(LiveMessage.fromByteArray('A:x').name(), 'x')

    def test_registration_replaces_listener(self):
        one = self.handle('B:reglistener', ('127.0.0.1', 10001))
        self.assertIs(self.server.listener, one)
        self.assertEqual(self.server.clientAddress, ('127.0.0.1', 10001))
        two = self.handle('B:reglistener', ('127.0.0.1', 10002))
        self.assertIs(self.server.listener, two)
        self.assertEqual(self.server.clientAddress, ('127.0.0.1', 10002))
        self.assertEqual(module.CommandHandler.rf433.dev.queued, [])

    def test_other_message_has_no_handler_or_response(self):
        sock = self.handle(LiveMessage('notice').toByteArray())
        self.assertEqual(sock.sent, [])
        self.assertIsNone(self.server.listener)
        self.assertEqual(module.CommandHandler.rf433.dev.queued, [])

    def test_incomplete_send_error_escapes_handler(self):
        self.assertRaises((TypeError, KeyError), self.handle,
                          LiveMessage('send').toByteArray())
        self.assertEqual(module.CommandHandler.rf433.dev.queued, [])

    def test_raw_event_and_bad_hex(self):
        self.server.listener = FakeSocket()
        self.server.clientAddress = ('127.0.0.1', 10001)
        self.server.rf433RawData({'data':'1a'})
        self.assertEqual(len(self.server.listener.sent), 1)
        self.assertEqual(LiveMessage.fromByteArray(
            self.server.listener.sent[0][0]).name(), 'rawdata')
        self.assertRaises(ValueError, self.server.rf433RawData, {'data':'not-hex'})

    def test_zwave_only_outbound_version_notice(self):
        self.server.listener = FakeSocket()
        self.server.clientAddress = ('127.0.0.1', 10001)
        self.server.zwave = FakeZWave()
        self.server.sendVersion()
        self.assertEqual(len(self.server.listener.sent), 1)
        self.assertEqual(LiveMessage.fromByteArray(
            self.server.listener.sent[0][0]).name(), 'zwaveinfo')

if __name__ == '__main__': unittest.main(verbosity=2)

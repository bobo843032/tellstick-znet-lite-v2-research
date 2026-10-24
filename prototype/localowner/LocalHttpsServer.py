# -*- coding: utf-8 -*-
"""Offline-review replacement for stock web Server: same router, HTTPS only.
No real device installation. Requires owner-supplied TLS cert and key.
"""
import os
import stat
import cherrypy
from base import Application, Plugin
from web.base.Server import RequestHandler, WebSocketHandler
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool

class LocalHttpsServer(Plugin):
    def __init__(self):
        cert = os.environ.get('LOCALOWNER_TLS_CERT', '/etc/telldus/local-https-cert.pem')
        key = os.environ.get('LOCALOWNER_TLS_KEY', '/etc/telldus/local-https-key.pem')
        for path in (cert, key):
            if not os.path.isfile(path):
                raise RuntimeError('HTTPS certificate or key missing')
        if os.stat(key).st_mode & 0077:
            raise RuntimeError('HTTPS private key must be mode 0600')
        host = os.environ.get('LOCALOWNER_TLS_HOST', '::')
        port = int(os.environ.get('LOCALOWNER_TLS_PORT', '443' if os.getuid() == 0 else '8443'))
        cherrypy.config.update({
            'server.socket_host': host,
            'server.socket_port': port,
            'server.ssl_module': 'builtin',
            'server.ssl_certificate': cert,
            'server.ssl_private_key': key,
            'tools.sessions.on': True,
            'tools.sessions.timeout': 60,
            'tools.sessions.httponly': True,
            'tools.sessions.secure': True,
        })
        cherrypy.tree.mount(RequestHandler(self.context), '', config={
            '/ws': {'tools.websocket.on': True, 'tools.websocket.handler_cls': WebSocketHandler}})
        cherrypy.engine.autoreload.unsubscribe()
        WebSocketPlugin(cherrypy.engine).subscribe()
        cherrypy.tools.websocket = WebSocketTool()
        cherrypy.engine.start()
        Application().registerShutdown(self.stop)
    @staticmethod
    def stop():
        cherrypy.engine.exit()

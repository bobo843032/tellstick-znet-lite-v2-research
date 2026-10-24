# -*- coding: utf-8 -*-
# Isolated, loopback-only stock CherryPy 3.7 TLS probe under MIPS Python2.
import os
import cherrypy
class Probe(object):
    @cherrypy.expose
    def index(self):
        return 'synthetic-tls-ok'
cherrypy.config.update({
    'environment':'production',
    'server.socket_host':'127.0.0.1',
    'server.socket_port':18443,
    'server.ssl_module':'builtin',
    'server.ssl_certificate':os.environ['TLS_TEST_CERT'],
    'server.ssl_private_key':os.environ['TLS_TEST_KEY'],
})
cherrypy.quickstart(Probe())

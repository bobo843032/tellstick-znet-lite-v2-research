# -*- coding: utf-8 -*-
"""Offline prototype for the stock Python 2.7 plugin interfaces.
Not installed on a TellStick. HTTPS must be configured before use.
"""
import base64
import cgi
import hashlib
import hmac
import json
import os
import stat
import time
import threading

import cherrypy
from api import ApiManager
from base import Plugin, implements
from web.base import IWebRequestAuthenticationHandler, IWebRequestHandler
from web.base.Server import WebResponse

OWNER_FILE = os.environ.get('LOCALOWNER_FILE', '/etc/telldus/local-owner.json')
SESSION_SECONDS = 1800
REQUEST_SECONDS = 600
ALLOWED_TTL_MINUTES = (1440, 10080, 40320, 525600)

class HtmlResponse(WebResponse):
    def __init__(self, page, code=200):
        WebResponse.__init__(self, code)
        self.data = page.encode('utf-8')
    def output(self, response):
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'

def safe(value):
    return cgi.escape(str(value), quote=True)

def csrf_value():
    return base64.urlsafe_b64encode(os.urandom(24)).rstrip('=')

def valid_csrf(provided, expected):
    if not provided or not expected:
        return False
    return hmac.compare_digest(str(provided), str(expected))

class LocalOwnerAuth(Plugin):
    implements(IWebRequestAuthenticationHandler, IWebRequestHandler)

    def __init__(self):
        self._owner = None
        self._owner_mtime = None
        self._failures = {}
        self._failure_lock = threading.RLock()

    def _load_owner(self):
        info = os.stat(OWNER_FILE)
        if not stat.S_ISREG(info.st_mode) or info.st_mode & 0077:
            raise ValueError('Owner credential file must be regular and mode 0600')
        if info.st_uid not in (0, os.geteuid()):
            raise ValueError('Owner credential file has unexpected owner')
        if self._owner is None or self._owner_mtime != info.st_mtime:
            with open(OWNER_FILE, 'rb') as handle:
                obj = json.load(handle)
            if obj.get('algorithm') != 'pbkdf2-sha256' or not 200000 <= int(obj.get('iterations', 0)) <= 1000000:
                raise ValueError('Unsupported owner verifier')
            self._owner = obj
            self._owner_mtime = info.st_mtime
        return self._owner

    def _remote_ip(self):
        try:
            return cherrypy.request.remote.ip
        except Exception:
            return 'unknown'

    def _login_allowed(self, ip):
        with self._failure_lock:
            count, last = self._failures.get(ip, (0, 0))
            if time.time() - last >= 300:
                self._failures.pop(ip, None)
                return True
            return count < 5

    def _record_login(self, ip, ok):
        with self._failure_lock:
            if ok:
                self._failures.pop(ip, None)
                return
            count, last = self._failures.get(ip, (0, 0))
            if time.time() - last >= 300:
                count = 0
            self._failures[ip] = (count + 1, time.time())
            # Bound memory use if arbitrary clients make failed attempts.
            if len(self._failures) > 256:
                oldest = min(self._failures, key=lambda x: self._failures[x][1])
                self._failures.pop(oldest, None)

    def _check_password(self, password):
        owner = self._load_owner()
        salt = base64.b64decode(owner['salt'])
        expected = base64.b64decode(owner['verifier'])
        value = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, int(owner['iterations']))
        return hmac.compare_digest(value, expected)

    def isUrlAuthorized(self, request):
        if not self._secure():
            return False
        # Local session must not authorize stock CSRF-unprotected approval POST.
        if cherrypy.request.path_info == '/api/authorize' and request.method() == 'POST':
            return False
        return bool(request.session('localowner_authenticated', False) and
                    request.session('localowner_until', 0) > time.time())

    def handleAuthenticationForUrl(self, request):
        return False

    def loginProvider(self):
        return {'name': 'Local owner (HTTPS only)', 'url': '/localowner/login'}

    def getMenuItems(self):
        return []

    def getTemplatesDirs(self):
        return []

    def matchRequest(self, plugin, path):
        return plugin == 'localowner' and path in ('login', 'logout', 'approve', 'dashboard')

    def requireAuthentication(self, plugin, path):
        # Each handler below performs its own owner/session/CSRF checks.
        return False

    def _page(self, title, body, code=200):
        return HtmlResponse('<!doctype html><html><head><meta charset="utf-8">'
                            '<meta name="viewport" content="width=device-width,initial-scale=1">'
                            '<title>%s</title></head><body><main><h1>%s</h1>%s</main></body></html>'
                            % (safe(title), safe(title), body), code)

    def _secure(self):
        # Never trust an unverified X-Forwarded-Proto client header.
        try:
            return cherrypy.request.scheme == 'https'
        except Exception:
            return False

    def handleRequest(self, plugin, path, params, request, **kwargs):
        if not self._secure():
            return self._page('HTTPS required', '<p>Local owner login is disabled on HTTP.</p>', 403)
        if path == 'dashboard':
            if not self.isUrlAuthorized(request):
                return self._page('Owner login required', '', 403)
            dashboard = os.path.join(os.path.dirname(__file__), 'local-ui.html')
            with open(dashboard, 'rb') as handle:
                return HtmlResponse(handle.read().decode('utf-8'))
        if path == 'login':
            if request.method() == 'GET':
                nonce = csrf_value()
                request.setSession('localowner_login_csrf', nonce)
                return self._page('Local owner login',
                    '<form method="post"><input type="hidden" name="csrf" value="%s">'
                    '<label>Password <input type="password" name="password" required></label>'
                    '<button type="submit">Log in</button></form>' % safe(nonce))
            if request.method() != 'POST':
                return self._page('Invalid method', '', 405)
            if not valid_csrf(request.post('csrf'), request.session('localowner_login_csrf')):
                return self._page('Rejected', '<p>Invalid form token.</p>', 403)
            request.setSession('localowner_login_csrf', None)
            ip = self._remote_ip()
            if not self._login_allowed(ip):
                return self._page('Try later', '<p>Too many login attempts.</p>', 429)
            try:
                ok = self._check_password(request.post('password', ''))
            except (IOError, OSError, ValueError, KeyError, TypeError):
                ok = False
            self._record_login(ip, ok)
            if not ok:
                return self._page('Rejected', '<p>Invalid owner credential.</p>', 403)
            cherrypy.session.regenerate()
            request.setSession('localowner_authenticated', True)
            request.setSession('localowner_until', time.time()+SESSION_SECONDS)
            return self._page('Logged in', '<p>Local owner session active.</p>'
                              '<p><a href="/localowner/dashboard">Open local dashboard</a></p>'
                              '<p>Open /localowner/approve?token=REQUEST_ID to approve a pending API request.</p>')
        if path == 'logout':
            if not self.isUrlAuthorized(request):
                return self._page('Rejected', '', 403)
            if request.method() == 'GET':
                nonce = csrf_value()
                request.setSession('localowner_logout_csrf', nonce)
                return self._page('Log out',
                    '<form method="post"><input type="hidden" name="csrf" value="%s">'
                    '<button type="submit">Log out</button></form>' % safe(nonce))
            if request.method() != 'POST' or not valid_csrf(
                    request.post('csrf'), request.session('localowner_logout_csrf')):
                return self._page('Rejected', '', 403)
            request.setSession('localowner_authenticated', False)
            request.setSession('localowner_until', 0)
            request.setSession('localowner_logout_csrf', None)
            cherrypy.session.regenerate()
            return self._page('Logged out', '<p>Local session invalidated.</p>')
        if path == 'approve':
            if not self.isUrlAuthorized(request):
                return self._page('Owner login required', '', 403)
            token = params.get('token', '')
            manager = ApiManager(self.context)  # Real stock ApiManager instance.
            pending = manager.tokens.get(token)
            if not pending or pending.get('authorized') or pending.get('created_local', 0) + REQUEST_SECONDS < time.time():
                # Stock PUT does not set created_local. First view starts local deadline.
                if not pending or pending.get('authorized'):
                    return self._page('Unknown request', '', 404)
            if 'created_local' not in pending:
                pending['created_local'] = time.time()
            if pending['created_local'] + REQUEST_SECONDS <= time.time():
                return self._page('Expired request', '', 403)
            if request.method() == 'GET':
                nonce = csrf_value()
                request.setSession('localowner_approve_csrf', nonce)
                options = ''.join('<option value="%d">%d minutes</option>' % (t,t) for t in ALLOWED_TTL_MINUTES)
                return self._page('Approve API token',
                    '<p>Application: %s</p><form method="post">'
                    '<input type="hidden" name="csrf" value="%s">'
                    '<label>Lifetime <select name="ttl">%s</select></label>'
                    '<label>Renewable <input type="checkbox" name="extend" value="1"></label>'
                    '<button type="submit">Approve</button></form>' %
                    (safe(pending.get('app', '')), safe(nonce), options))
            if request.method() != 'POST':
                return self._page('Invalid method', '', 405)
            if not valid_csrf(request.post('csrf'), request.session('localowner_approve_csrf')):
                return self._page('Rejected', '<p>Invalid form token.</p>', 403)
            try:
                ttl = int(request.post('ttl'))
            except (TypeError, ValueError):
                return self._page('Rejected', '<p>Invalid lifetime.</p>', 400)
            if ttl not in ALLOWED_TTL_MINUTES:
                return self._page('Rejected', '<p>Lifetime not allowed.</p>', 400)
            pending['authorized'] = True
            pending['allowRenew'] = request.post('extend') == '1'
            pending['ttl'] = ttl * 60
            request.setSession('localowner_approve_csrf', None)
            return self._page('Approved', '<p>The requesting application may now fetch its token.</p>')
        return self._page('Not found', '', 404)

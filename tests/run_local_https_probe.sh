#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
: "${FIRMWARE_ROOTFS:?Set FIRMWARE_ROOTFS to an independently obtained, extracted firmware 1.3.2 rootfs}"
: "${QEMU_MIPS:?Set QEMU_MIPS to a compatible qemu-mips executable}"
ROOTFS="$(readlink -f "$FIRMWARE_ROOTFS")"
QEMU="$(readlink -f "$QEMU_MIPS")"
TEMP_DIR="$(mktemp -d "$ROOT/tests/local-https.XXXXXX")"
PID=""
cleanup() {
  if [ -n "$PID" ]; then kill -KILL "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true; fi
  rm -rf "$TEMP_DIR"
}
trap cleanup EXIT HUP INT TERM
openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj /CN=127.0.0.1 \
  -addext subjectAltName=IP:127.0.0.1 \
  -keyout "$TEMP_DIR/key.pem" -out "$TEMP_DIR/cert.pem" >/dev/null 2>&1
chmod 600 "$TEMP_DIR/key.pem"
python3 - "$TEMP_DIR/owner.json" <<'PY'
import base64,hashlib,json,os,sys
salt=b"synthetic-offline-salt"
digest=hashlib.pbkdf2_hmac("sha256",b"synthetic-password-1234",salt,200000)
path=sys.argv[1]
with open(path,"w") as f:
    json.dump({"algorithm":"pbkdf2-sha256","iterations":200000,
               "salt":base64.b64encode(salt).decode(),
               "verifier":base64.b64encode(digest).decode()},f)
os.chmod(path,0o600)
PY
cd "$ROOT"
LOCALOWNER_TLS_CERT="$TEMP_DIR/cert.pem" LOCALOWNER_TLS_KEY="$TEMP_DIR/key.pem" \
  LOCALOWNER_TLS_HOST=127.0.0.1 LOCALOWNER_TLS_PORT=18444 \
  LOCALOWNER_FILE="$TEMP_DIR/owner.json" \
  "$QEMU" -L "$ROOTFS" \
  -E PYTHONHOME="$ROOTFS/usr" \
  -E PYTHONPATH="$ROOT/prototype" \
  "$ROOTFS/usr/bin/python2.7" "$ROOT/tests/local_https_server_probe.py" \
  >"$TEMP_DIR/server.log" 2>&1 &
PID=$!
i=0
while [ "$i" -lt 50 ]; do
  if curl --silent --fail --cacert "$TEMP_DIR/cert.pem" \
    -c "$TEMP_DIR/cookies" -b "$TEMP_DIR/cookies" \
    https://127.0.0.1:18444/localowner/login >"$TEMP_DIR/login.html" 2>/dev/null; then break; fi
  if ! kill -0 "$PID" 2>/dev/null; then break; fi
  i=$((i+1)); sleep 0.2
done
grep -q "Local owner login" "$TEMP_DIR/login.html" || { tail -8 "$TEMP_DIR/server.log"; exit 1; }
if curl --silent --max-time 2 http://127.0.0.1:18444/localowner/login \
  >"$TEMP_DIR/plain" 2>/dev/null && grep -q "Local owner login" "$TEMP_DIR/plain"; then
  echo "Plain HTTP exposed owner login: FAIL"; exit 1
fi
# Dashboard must reject a client without owner session.
unauth="$(curl --silent --output /dev/null --write-out '%{http_code}' \
  --cacert "$TEMP_DIR/cert.pem" https://127.0.0.1:18444/localowner/dashboard)"
test "$unauth" = 403
csrf="$(sed -n 's/.*name="csrf" value="\([^"]*\)".*/\1/p' "$TEMP_DIR/login.html")"
test -n "$csrf"
login_code="$(curl --silent --output "$TEMP_DIR/after.html" --write-out '%{http_code}' \
  --cacert "$TEMP_DIR/cert.pem" -c "$TEMP_DIR/cookies" -b "$TEMP_DIR/cookies" \
  --data-urlencode "csrf=$csrf" --data-urlencode "password=synthetic-password-1234" \
  https://127.0.0.1:18444/localowner/login)"
test "$login_code" = 200
grep -q "Logged in" "$TEMP_DIR/after.html"
dashboard_code="$(curl --silent --output "$TEMP_DIR/dashboard.html" --write-out '%{http_code}' \
  --cacert "$TEMP_DIR/cert.pem" -c "$TEMP_DIR/cookies" -b "$TEMP_DIR/cookies" \
  https://127.0.0.1:18444/localowner/dashboard)"
test "$dashboard_code" = 200
grep -q "TellStick Local" "$TEMP_DIR/dashboard.html"
request_code="$(curl --silent --output "$TEMP_DIR/request.json" --write-out '%{http_code}' \
  --cacert "$TEMP_DIR/cert.pem" --request PUT --data-urlencode 'app=synthetic-browser' \
  https://127.0.0.1:18444/api/token)"
test "$request_code" = 200
req="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["token"])' "$TEMP_DIR/request.json")"
test -n "$req"
auth_url="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["authUrl"])' "$TEMP_DIR/request.json")"
test "$auth_url" = "https://127.0.0.1:18444/localowner/approve?token=$req"
approve_code="$(curl --silent --output "$TEMP_DIR/approve.html" --write-out '%{http_code}' \
  --cacert "$TEMP_DIR/cert.pem" -c "$TEMP_DIR/cookies" -b "$TEMP_DIR/cookies" \
  "https://127.0.0.1:18444/localowner/approve?token=$req")"
test "$approve_code" = 200
approval_csrf="$(sed -n 's/.*name="csrf" value="\([^"]*\)".*/\1/p' "$TEMP_DIR/approve.html")"
test -n "$approval_csrf"
approve_post_code="$(curl --silent --output "$TEMP_DIR/approved.html" --write-out '%{http_code}' \
  --cacert "$TEMP_DIR/cert.pem" -c "$TEMP_DIR/cookies" -b "$TEMP_DIR/cookies" \
  --data-urlencode "csrf=$approval_csrf" --data-urlencode 'ttl=1440' \
  --data-urlencode 'extend=1' \
  "https://127.0.0.1:18444/localowner/approve?token=$req")"
test "$approve_post_code" = 200
grep -q 'Approved' "$TEMP_DIR/approved.html"
token_code="$(curl --silent --output "$TEMP_DIR/token.json" --write-out '%{http_code}' \
  --cacert "$TEMP_DIR/cert.pem" "https://127.0.0.1:18444/api/token?token=$req")"
test "$token_code" = 200
jwt="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["token"])' "$TEMP_DIR/token.json")"
system_code="$(curl --silent --output "$TEMP_DIR/system.json" --write-out '%{http_code}' \
  --cacert "$TEMP_DIR/cert.pem" -H "Authorization: Bearer $jwt" \
  https://127.0.0.1:18444/api/system/info)"
test "$system_code" = 200
grep -q 'synthetic-znet' "$TEMP_DIR/system.json"
for route in devices/list sensors/list device/turnOn?id=12; do
  name="$(printf '%s' "$route" | tr '/?' '__')"
  code="$(curl --silent --output "$TEMP_DIR/$name.json" --write-out '%{http_code}' \
    --cacert "$TEMP_DIR/cert.pem" -H "Authorization: Bearer $jwt" \
    "https://127.0.0.1:18444/api/$route")"
  test "$code" = 200
done
grep -q 'Synthetic switch' "$TEMP_DIR/devices_list.json"
grep -q 'Synthetic sensor' "$TEMP_DIR/sensors_list.json"
grep -q 'success' "$TEMP_DIR/device_turnOn_id=12.json"
logout_get="$(curl --silent --output "$TEMP_DIR/logout.html" --write-out '%{http_code}' \
  --cacert "$TEMP_DIR/cert.pem" -c "$TEMP_DIR/cookies" -b "$TEMP_DIR/cookies" \
  https://127.0.0.1:18444/localowner/logout)"
test "$logout_get" = 200
logout_csrf="$(sed -n 's/.*name="csrf" value="\([^"]*\)".*/\1/p' "$TEMP_DIR/logout.html")"
test -n "$logout_csrf"
logout_post="$(curl --silent --output "$TEMP_DIR/logged-out.html" --write-out '%{http_code}' \
  --cacert "$TEMP_DIR/cert.pem" -c "$TEMP_DIR/cookies" -b "$TEMP_DIR/cookies" \
  --data-urlencode "csrf=$logout_csrf" https://127.0.0.1:18444/localowner/logout)"
test "$logout_post" = 200
after_logout="$(curl --silent --output /dev/null --write-out '%{http_code}' \
  --cacert "$TEMP_DIR/cert.pem" -c "$TEMP_DIR/cookies" -b "$TEMP_DIR/cookies" \
  https://127.0.0.1:18444/localowner/dashboard)"
test "$after_logout" = 403
curl --silent --fail --cacert "$TEMP_DIR/cert.pem" --request PUT \
  --data-urlencode 'app=second-synthetic-client' \
  https://127.0.0.1:18444/api/token >"$TEMP_DIR/request2.json"
auth_url2="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["authUrl"])' "$TEMP_DIR/request2.json")"
req2="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["token"])' "$TEMP_DIR/request2.json")"
unauth_approval="$(curl --silent --output /dev/null --write-out '%{http_code}' \
  --cacert "$TEMP_DIR/cert.pem" -c "$TEMP_DIR/cookies" -b "$TEMP_DIR/cookies" "$auth_url2")"
test "$unauth_approval" = 303
curl --silent --fail --cacert "$TEMP_DIR/cert.pem" \
  -c "$TEMP_DIR/cookies" -b "$TEMP_DIR/cookies" \
  https://127.0.0.1:18444/localowner/login >"$TEMP_DIR/login2.html"
csrf2="$(sed -n 's/.*name="csrf" value="\([^"]*\)".*/\1/p' "$TEMP_DIR/login2.html")"
test -n "$csrf2"
login_redirect="$(curl --silent --output /dev/null --write-out '%{http_code}' \
  --cacert "$TEMP_DIR/cert.pem" -c "$TEMP_DIR/cookies" -b "$TEMP_DIR/cookies" \
  --data-urlencode "csrf=$csrf2" --data-urlencode "password=synthetic-password-1234" \
  https://127.0.0.1:18444/localowner/login)"
test "$login_redirect" = 303
curl --silent --fail --cacert "$TEMP_DIR/cert.pem" \
  -c "$TEMP_DIR/cookies" -b "$TEMP_DIR/cookies" \
  "$auth_url2" >"$TEMP_DIR/approval2.html"
grep -q 'Approve API token' "$TEMP_DIR/approval2.html"
if [ "${LOCALOWNER_LOCAL_ONLY:-0}" = 1 ]; then
  # A local owner session cannot authorize the stock, CSRF-unprotected route.
  stock_approval="$(curl --silent --output /dev/null --write-out '%{http_code}' \
    --cacert "$TEMP_DIR/cert.pem" -c "$TEMP_DIR/cookies" -b "$TEMP_DIR/cookies" \
    --data-urlencode "token=$req2" --data-urlencode 'ttl=1440' \
    https://127.0.0.1:18444/api/authorize)"
  test "$stock_approval" = 303
fi
echo "local provider HTTPS, owner login, token approval, stock JWT/API: PASS"

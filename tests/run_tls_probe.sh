#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
: "${FIRMWARE_ROOTFS:?Set FIRMWARE_ROOTFS to an independently obtained, extracted firmware 1.3.2 rootfs}"
: "${QEMU_MIPS:?Set QEMU_MIPS to a compatible qemu-mips executable}"
ROOTFS="$(readlink -f "$FIRMWARE_ROOTFS")"
QEMU="$(readlink -f "$QEMU_MIPS")"
TEMP_DIR="$(mktemp -d "$ROOT/tests/tls-probe.XXXXXX")"
PID=""
cleanup() {
  if [ -n "$PID" ]; then kill "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true; fi
  rm -rf "$TEMP_DIR"
}
trap cleanup EXIT HUP INT TERM
openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj /CN=127.0.0.1 \
  -addext subjectAltName=IP:127.0.0.1 \
  -keyout "$TEMP_DIR/key.pem" -out "$TEMP_DIR/cert.pem" >/dev/null 2>&1
chmod 600 "$TEMP_DIR/key.pem"
cd "$ROOT"
TLS_TEST_CERT="$TEMP_DIR/cert.pem" TLS_TEST_KEY="$TEMP_DIR/key.pem" \
  "$QEMU" -L "$ROOTFS" \
  -E PYTHONHOME="$ROOTFS/usr" \
  "$ROOTFS/usr/bin/python2.7" "$ROOT/tests/tls_probe.py" \
  >"$TEMP_DIR/server.log" 2>&1 &
PID=$!
i=0
while [ "$i" -lt 30 ]; do
  if curl --silent --show-error --fail --cacert "$TEMP_DIR/cert.pem" \
    https://127.0.0.1:18443/ >"$TEMP_DIR/response" 2>/dev/null; then
    test "$(cat "$TEMP_DIR/response")" = "synthetic-tls-ok"
    echo "stock CherryPy 3.7 builtin TLS: PASS"
    exit 0
  fi
  if ! kill -0 "$PID" 2>/dev/null; then break; fi
  i=$((i+1))
  sleep 0.2
done
echo "stock CherryPy 3.7 builtin TLS: FAIL"
tail -8 "$TEMP_DIR/server.log"
exit 1

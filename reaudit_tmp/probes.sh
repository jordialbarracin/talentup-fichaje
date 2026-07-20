#!/usr/bin/env bash
set -e
BASE="http://localhost:8000/api"

echo "0. Health"
curl -s "$BASE/health" | python3 -m json.tool

echo "1. CSP nonce"
curl -s -D - "$BASE/health" -o /dev/null | grep -i "content-security-policy"

echo "2. Body limit 413"
python3 -c "
import json, os
obj = {'payload': 'a' * (1024 * 1100)}
os.makedirs('/d/talentup-fichaje/reaudit_tmp', exist_ok=True)
open('/d/talentup-fichaje/reaudit_tmp/huge.json','w').write(json.dumps(obj))
"
curl -s -o /dev/null -w "%{http_code}\n" \
  -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  --data-binary @/d/talentup-fichaje/reaudit_tmp/huge.json
rm -f /d/talentup-fichaje/reaudit_tmp/huge.json

echo "3. XSS storage test"
curl -s -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"restaurant_name":"XSSTest","owner_name":"<script>alert(1)</script>","email":"xss8@example.com","password":"xsspass123"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(repr(d['user']['name']))"

echo "4. SQLi login probe"
curl -s -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com'"'"' OR '"'"'1'"'"'='"'"'1","password":"x"}' \
  | python3 -m json.tool

echo "5. JWT tampering"
TOKEN=$(curl -s -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"restaurant_name":"JWTTest","owner_name":"JWT","email":"jwt8@example.com","password":"jwtpass123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
F=$(python3 - <<PY
import base64, hmac, hashlib, json
h, p, s = "$TOKEN".split('.')
payload = json.loads(base64.urlsafe_b64decode(p + '='*(-len(p)%4)).decode())
fake_payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
fake_sig = base64.urlsafe_b64encode(
    hmac.new(b'fake', f"{h}.{fake_payload_b64}".encode(), hashlib.sha256).digest()
).decode().rstrip('=')
print(f"{h}.{fake_payload_b64}.{fake_sig}")
PY
)
curl -s -o /dev/null -w "%{http_code}\n" "$BASE/auth/me" -H "Authorization: Bearer $F"

echo "6. Refresh tokens"
REFRESH=$(curl -s -X POST "$BASE/auth/register" -H "Content-Type: application/json" \
  -d '{"restaurant_name":"Refresh","owner_name":"Refresh","email":"refresh8@example.com","password":"refreshpass123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['refresh_token'])")
curl -s -X POST "$BASE/auth/refresh" \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$REFRESH\"}" | python3 -m json.tool

echo "7. Cross-tenant isolation"
A=$(curl -s -X POST "$BASE/auth/register" -H "Content-Type: application/json" \
  -d '{"restaurant_name":"TenantA8","owner_name":"A","email":"a8@example.com","password":"tenantpass123"}')
B=$(curl -s -X POST "$BASE/auth/register" -H "Content-Type: application/json" \
  -d '{"restaurant_name":"TenantB8","owner_name":"B","email":"b8@example.com","password":"tenantpass123"}')
TOKEN_A=$(echo "$A" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
TOKEN_B=$(echo "$B" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
TENANT_A=$(echo "$A" | python3 -c "import sys,json; print(json.load(sys.stdin)['tenant_id'])")
EMP_A=$(curl -s -X POST "$BASE/employees" \
  -H "Authorization: Bearer $TOKEN_A" -H "Content-Type: application/json" \
  -d '{"name":"Employee A8","pin":"1234","clock_method":"pin"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")
curl -s -o /dev/null -w "%{http_code}\n" "$BASE/employees/$EMP_A" -H "Authorization: Bearer $TOKEN_B"

echo "8. Rate limiting NFC 15x"
NFC_REG=$(curl -s -X POST "$BASE/auth/register" -H "Content-Type: application/json" \
  -d '{"restaurant_name":"NFCRest8","owner_name":"NFC","email":"nfc8@example.com","password":"nfcpass123"}')
TOKEN_NFC=$(echo "$NFC_REG" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
TENANT_NFC=$(echo "$NFC_REG" | python3 -c "import sys,json; print(json.load(sys.stdin)['tenant_id'])")
curl -s -X POST "$BASE/employees" -H "Authorization: Bearer $TOKEN_NFC" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"NFC Emp8\",\"pin\":\"1234\",\"nfc_uid\":\"A1B2C3D4\",\"clock_method\":\"nfc\"}" > /dev/null
for i in $(seq 1 15); do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST "$BASE/clock/nfc" \
    -H "Content-Type: application/json" \
    -d "{\"tenant_id\":\"$TENANT_NFC\",\"nfc_uid\":\"A1B2C3D4\"}"
done

echo "9. Rate limiting PIN 15x"
PIN_REG=$(curl -s -X POST "$BASE/auth/register" -H "Content-Type: application/json" \
  -d '{"restaurant_name":"PINRest8","owner_name":"PIN","email":"pin8@example.com","password":"pinpass123"}')
TOKEN_PIN=$(echo "$PIN_REG" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
TENANT_PIN=$(echo "$PIN_REG" | python3 -c "import sys,json; print(json.load(sys.stdin)['tenant_id'])")
curl -s -X POST "$BASE/employees" -H "Authorization: Bearer $TOKEN_PIN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"PIN Emp8\",\"pin\":\"9876\",\"clock_method\":\"pin\"}" > /dev/null
for i in $(seq 1 15); do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST "$BASE/clock" \
    -H "Content-Type: application/json" \
    -d "{\"tenant_id\":\"$TENANT_PIN\",\"pin\":\"9876\",\"type\":\"in\"}"
done

echo "10. Stripe webhook without signature"
curl -s -o /dev/null -w "%{http_code}\n" -X POST "$BASE/billing/webhook" \
  -H "Content-Type: application/json" \
  -d '{"type":"checkout.session.completed"}'

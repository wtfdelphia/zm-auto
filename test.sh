BASE="https://mail.coco888.dpdns.org"
ADMIN_AUTH="sailing2018."

RESP=$(curl -s -X POST "$BASE/admin/new_address" \
  -H "x-admin-auth: $ADMIN_AUTH" \
  -H "Content-Type: application/json" \
  -d '{
    "enablePrefix": true,
    "name": "wtftest1",
    "domain": "mail.coco888.dpdns.org"
  }')


 echo "$RESP" | jq


JWT=$(echo "$RESP" | jq -r '.jwt')
ADDR=$(echo "$RESP" | jq -r '.address')

echo “$ADDR"


curl -s "$BASE/api/settings" \
  -H "Authorization: Bearer $JWT" | jq



curl -s "$BASE/api/parsed_mails?limit=20&offset=0" \
  -H "Authorization: Bearer $JWT" | jq



sk-ai-v1-09786378b12a51a1c301bc93941295922d1900feeb06ae35e72a65fe09d97740

sk-ai-v1-7865b781ca1334d19fa4e625faa354d611d31e398bcde41fbe8483b164a46e1b



wtf26888@cc.adu.edu.rs


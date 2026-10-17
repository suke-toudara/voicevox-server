# プログラムから呼ぶ

以下の例では、自己署名証明書を使っている前提で証明書の確認を省いています（curl の `-k` と同じ）。証明書を確認させる方法は [簡易：自己署名証明書](https-self-signed.md#クライアントに証明書を信用させる) を見てください。

## Python（requests）

```python
import requests

requests.post(
    "https://192.168.0.10:8443/speak",
    headers={"Authorization": "Bearer <TOKEN>"},
    json={"text": "処理が終わりました", "speaker": 3},
    verify=False,  # 自己署名なので確認を省く。証明書を渡すなら verify="server.crt"
    timeout=5,
)
```

## Python（標準ライブラリのみ）

```python
import json, ssl, urllib.request

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request(
    "https://192.168.0.10:8443/speak",
    data=json.dumps({"text": "処理が終わりました"}).encode(),
    headers={"Authorization": "Bearer <TOKEN>", "Content-Type": "application/json"},
    method="POST",
)
urllib.request.urlopen(req, context=ctx, timeout=5)
```

## JavaScript（Node.js）

```js
process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0"; // 自己署名なので確認を省く

await fetch("https://192.168.0.10:8443/speak", {
  method: "POST",
  headers: {
    "Authorization": "Bearer <TOKEN>",
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ text: "処理が終わりました" }),
});
```

## シェル：コマンドが終わったら知らせる

```bash
say() {
  curl -sk -X POST https://192.168.0.10:8443/speak \
    -H "Authorization: Bearer $VV_TOKEN" \
    -H "Content-Type: text/plain" --data-binary "$1" >/dev/null
}

make build && say "ビルドが終わりました" || say "ビルドに失敗しました"
```

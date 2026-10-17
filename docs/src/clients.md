# プログラムから呼ぶ

## Python（requests）

```python
import requests

requests.post(
    "http://192.168.0.10:8080/speak",
    json={"text": "処理が終わりました", "speaker": 3},
    timeout=60,  # 読み上げが終わるまで返事が来ないので長めに
)
```

## Python（標準ライブラリのみ）

```python
import json, urllib.request

req = urllib.request.Request(
    "http://192.168.0.10:8080/speak",
    data=json.dumps({"text": "処理が終わりました"}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
urllib.request.urlopen(req, timeout=60)
```

## JavaScript（Node.js）

```js
await fetch("http://192.168.0.10:8080/speak", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ text: "処理が終わりました" }),
});
```

## 待たずに次へ進みたいとき

返事は読み上げが終わってから来ます。待たずに処理を続けたいときは `"wait": false` を付けます。

```bash
curl -X POST http://192.168.0.10:8080/speak \
  -H "Content-Type: application/json" \
  -d '{"text":"処理を開始します","wait":false}'
```

## シェル：コマンドが終わったら知らせる

```bash
say() {
  curl -s -X POST http://192.168.0.10:8080/speak \
    -H "Content-Type: text/plain" --data-binary "$1" >/dev/null
}

make build && say "ビルドが終わりました" || say "ビルドに失敗しました"
```

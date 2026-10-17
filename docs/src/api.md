# API リファレンス

ベース URL: `https://<host>:8443`

| メソッド | パス | 認証 | 内容 |
|---|---|---|---|
| `POST` | `/speak` | 必要 | テキストをしゃべらせる |
| `GET` | `/speakers` | 必要 | 話者とスタイル ID の一覧 |
| `GET` | `/health` | 不要 | wrapper とエンジンの稼働確認 |

## 認証

`Authorization` ヘッダに合言葉（トークン）を付けます。

```text
Authorization: Bearer <VV_TOKEN の値>
```

URL に合言葉を含める方法（`?token=`）には対応していません。URL はブラウザの履歴やサーバーのログに残りやすいためです。

## POST /speak

テキストを再生キューに入れます。再生の終わりは待たずに、すぐ返事を返します。

### パラメータ

| 名前 | 型 | 必須 | 既定値 | 内容 |
|---|---|---|---|---|
| `text` | 文字列 | ○ | | しゃべる文（1000 文字まで） |
| `speaker` | 整数 | | `VV_SPEAKER`（3） | スタイル ID。`/speakers` で確認できます |
| `speed` | 数値 | | 1.0 | 話す速さ |
| `pitch` | 数値 | | 0.0 | 声の高さ |
| `intonation` | 数値 | | 1.0 | 抑揚の強さ |
| `volume` | 数値 | | 1.0 | 音量 |

### 送り方

本文の形式は 3 種類から選べます。

**JSON（おすすめ）**

```bash
curl -k -X POST https://localhost:8443/speak \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"こんにちは","speaker":3,"speed":1.2}'
```

**フォーム**

```bash
curl -k -X POST https://localhost:8443/speak \
  -H "Authorization: Bearer $TOKEN" \
  --data-urlencode "text=こんにちは" -d "speaker=3"
```

**テキストそのまま**

```bash
curl -k -X POST https://localhost:8443/speak \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: text/plain" \
  --data-binary "こんにちは"
```

> curl の `-d` は、何も指定しないとフォーム形式で送ります。テキストだけを送るときは `Content-Type: text/plain` を必ず付けてください。

### レスポンス

```json
{"status": "queued", "queue": 1, "text": "こんにちは", "speaker": 3}
```

| ステータス | 意味 |
|---|---|
| `202` | 受け付けた。少しあとに再生される |
| `400` | `text` が空、長すぎる、数値の項目が数値でない、本文が壊れている |
| `401` | 合言葉が違う、または付いていない |
| `404` | パスが違う |
| `405` | `GET /speak` が呼ばれた（`POST` を使ってください） |
| `503` | キューがいっぱい（50 件） |

## GET /speakers

```bash
curl -k -H "Authorization: Bearer $TOKEN" https://localhost:8443/speakers
```

```json
[
  {"name": "四国めたん", "styles": [{"id": 2, "name": "ノーマル"}, ...]},
  {"name": "ずんだもん", "styles": [{"id": 3, "name": "ノーマル"}, ...]}
]
```

`styles[].id` を `/speak` の `speaker` に指定します。

## GET /health

```bash
curl -k https://localhost:8443/health
```

| ステータス | 本文の例 |
|---|---|
| `200` | `{"status": "ok", "engine": "0.25.2", "queue": 0}` |
| `503` | `{"status": "engine unreachable", "error": "..."}` |

## REST API との関係

この API は「REST 風」の Web API です。データを JSON でやりとりし、結果を HTTP のステータスコードで返し、GET は「見るだけ」、POST は「何かを起こす」に使い分けています。

`/speak` は動詞なので、厳密な REST のお作法（URL は名詞にする）からは少し外れています。「しゃべって」という命令が名前から分かるほうが使いやすいので、あえてこの名前にしています。

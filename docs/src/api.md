# API リファレンス

ベース URL: `http://<host>:8080`

| メソッド | パス | 内容 |
|---|---|---|
| `POST` | `/speak` | テキストをしゃべらせる |
| `GET` | `/speakers` | 話者とスタイル ID の一覧 |
| `GET` | `/health` | wrapper とエンジンの稼働確認 |

## 認証（オプション）

既定では認証なしで、誰でも呼べます。

同じネットワークに知らない人がいて、勝手にしゃべらされたくない場合は、`.env` に合言葉を設定します。

```bash
# .env
VV_TOKEN=好きな合言葉
```

設定すると、`/speak` と `/speakers` を呼ぶときに `Authorization` ヘッダが必要になります（`/health` は不要のまま）。

> 通信は HTTP（暗号化なし）なので、同じネットワークで通信をのぞける人には合言葉も見えます。「うっかり鳴らされない」程度の目的で使ってください。

```bash
curl -X POST http://localhost:8080/speak \
  -H "Authorization: Bearer 好きな合言葉" \
  -H "Content-Type: application/json" \
  -d '{"text":"こんにちは"}'
```

## POST /speak

テキストをしゃべらせます。標準では **読み上げが終わってから** 返事を返します。

続けて送られた場合は順番待ちの列に入り、1 つずつ再生されます。前の読み上げが残っていると、その分も待つことになります。

### パラメータ

| 名前 | 型 | 必須 | 既定値 | 内容 |
|---|---|---|---|---|
| `text` | 文字列 | ○ | | しゃべる文（1000 文字まで） |
| `speaker` | 整数 | | `VV_SPEAKER`（3） | スタイル ID。`/speakers` で確認できます |
| `speed` | 数値 | | 1.0 | 話す速さ |
| `pitch` | 数値 | | 0.0 | 声の高さ |
| `intonation` | 数値 | | 1.0 | 抑揚の強さ |
| `volume` | 数値 | | 1.0 | 音量 |
| `wait` | 真偽値 | | `true` | `false` にすると、読み上げを待たずにすぐ返事を返す |

### 送り方

本文の形式は 3 種類から選べます。

**JSON（おすすめ）**

```bash
curl -X POST http://localhost:8080/speak \
  -H "Content-Type: application/json" \
  -d '{"text":"こんにちは","speaker":3,"speed":1.2}'
```

**フォーム**

```bash
curl -X POST http://localhost:8080/speak \
  --data-urlencode "text=こんにちは" -d "speaker=3"
```

**テキストそのまま**

```bash
curl -X POST http://localhost:8080/speak \
  -H "Content-Type: text/plain" \
  --data-binary "こんにちは"
```

> curl の `-d` は、何も指定しないとフォーム形式で送ります。テキストだけを送るときは `Content-Type: text/plain` を必ず付けてください。

### レスポンス

読み上げが終わったとき:

```json
{"status": "spoken", "text": "こんにちは", "speaker": 3}
```

`"wait": false` のとき（列に並べた時点で返す）:

```json
{"status": "queued", "queue": 1, "text": "こんにちは", "speaker": 3}
```

| ステータス | 意味 |
|---|---|
| `200` | 読み上げが終わった |
| `202` | 受け付けた（`"wait": false` のとき）。少しあとに再生される |
| `400` | `text` が空、長すぎる、数値の項目が数値でない、本文が壊れている |
| `401` | 合言葉が違う、または付いていない（`VV_TOKEN` を設定したときだけ） |
| `404` | パスが違う |
| `405` | `GET /speak` が呼ばれた（`POST` を使ってください） |
| `502` | 音声の生成か再生に失敗した（`"wait": false` のときは返らない） |
| `503` | キューがいっぱい（50 件） |
| `504` | `VV_WAIT_TIMEOUT` 秒待っても終わらなかった。読み上げ自体は列に残っていて、あとで再生される |

## GET /speakers

```bash
curl http://localhost:8080/speakers
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
curl http://localhost:8080/health
```

| ステータス | 本文の例 |
|---|---|
| `200` | `{"status": "ok", "engine": "0.25.2", "queue": 0}` |
| `503` | `{"status": "engine unreachable", "error": "..."}` |

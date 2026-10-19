# API リファレンス

ベース URL: `http://<host>:8080`

| メソッド | パス | 内容 |
|---|---|---|
| `POST` | `/speak` | テキストをしゃべらせる |
| `GET` | `/speakers` | 話者と話し方の一覧 |
| `GET` | `/settings` | いつもの設定を見る |
| `PUT` | `/settings` | いつもの設定を変える |
| `DELETE` | `/settings` | いつもの設定を初期値に戻す |
| `GET` | `/health` | wrapper とエンジンの稼働確認 |
| `GET` | `/` | [Web 画面](ui.md) |

## 認証（オプション）

既定では認証なしで、誰でも呼べます。

同じネットワークに知らない人がいて、勝手にしゃべらされたくない場合は、`.env` に合言葉を設定します。

```bash
# .env
VV_TOKEN=好きな合言葉
```

設定すると、`/health` と `/`（Web 画面）以外を呼ぶときに `Authorization` ヘッダが必要になります。

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

長い文章は「。」「！」「？」と改行で区切り、1 文ずつ音声を作って再生します。再生している間に次の文を作るので、全体ができあがるのを待たずにしゃべり始めます。CPU が遅く音声づくりが再生に追いつかない場合は、途中で止まらないよう、残りの文が間に合うだけの音声がたまってから再生を始めます。

### パラメータ

| 名前 | 型 | 必須 | 既定値 | 内容 |
|---|---|---|---|---|
| `text` | 文字列 | ○ | | しゃべる文（`max_text` 文字まで。初期値 1000） |
| `speaker` | 名前 / 整数 | | いつもの声 | 声。下の「声の指定」を参照 |
| `speed` | 数値 0.5〜2.0 | | いつもの設定 | 話す速さ |
| `pitch` | 数値 -0.15〜0.15 | | いつもの設定 | 声の高さ |
| `intonation` | 数値 0〜2.0 | | いつもの設定 | 抑揚の強さ |
| `volume` | 数値 0〜2.0 | | いつもの設定 | 音量 |
| `pre_silence` | 数値 0〜1.5 | | いつもの設定 | 文の前の無音（秒） |
| `post_silence` | 数値 0〜1.5 | | いつもの設定 | 文の後の無音（秒） |
| `pause` | 数値 0〜2.0 | | いつもの設定 | 句読点の間の長さ（倍率） |
| `wait` | 真偽値 | | `true` | `false` にすると、読み上げを待たずにすぐ返事を返す |

省略した項目は「いつもの設定」（[`/settings`](#get-settings) や [Web 画面](ui.md) で保存したもの）が使われます。

### 声の指定

`speaker` は 3 通りの書き方ができます。

| 書き方 | 例 | 意味 |
|---|---|---|
| 名前 | `"ずんだもん"` | そのキャラクターの「ノーマル」 |
| 名前/話し方 | `"ずんだもん/ささやき"` | 話し方まで指定 |
| 番号 | `3` | スタイル ID（`/speakers` で確認） |

名前や話し方が見つからないときは、しゃべらずに `400` を返します。返事の `choices` に使える名前の一覧が入ります。

```json
{"error": "unknown style for ずんだもん: 怒り", "choices": ["ノーマル", "あまあま", "ツンツン", ...]}
```

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
{"status": "spoken", "text": "こんにちは", "speaker": 3, "voice": "ずんだもん/ノーマル",
 "speed": 1.0, "pitch": 0.0, "intonation": 1.0, "volume": 1.0,
 "pre_silence": 0.1, "post_silence": 0.1, "pause": 1.0}
```

`"wait": false` のとき（列に並べた時点で返す）:

```json
{"status": "queued", "queue": 1, "text": "こんにちは", "speaker": 3, "voice": "ずんだもん/ノーマル", ...}
```

| ステータス | 意味 |
|---|---|
| `200` | 読み上げが終わった |
| `202` | 受け付けた（`"wait": false` のとき）。少しあとに再生される |
| `400` | `text` が空・長すぎる、声が見つからない、数値が範囲外、本文が壊れている |
| `401` | 合言葉が違う、または付いていない（`VV_TOKEN` を設定したときだけ） |
| `404` | パスが違う |
| `405` | `GET /speak` が呼ばれた（`POST` を使ってください） |
| `502` | 音声の生成か再生に失敗した（`"wait": false` のときは返らない） |
| `503` | キューがいっぱい（50 件）、またはエンジンにつながらない |
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

`speaker` には、`name`（例: `"ずんだもん"`）か `name/styles[].name`（例: `"ずんだもん/あまあま"`）か `styles[].id`（例: `1`）を指定します。歌専用の声は含まれません。

## GET /settings

いつもの設定（`speaker` などを省略したときに使われる値）を返します。

```bash
curl http://localhost:8080/settings
```

```json
{
  "settings": {"speaker": 3, "speed": 1.0, "pitch": 0.0, "intonation": 1.0, "volume": 1.0,
               "pre_silence": 0.1, "post_silence": 0.1, "pause": 1.0,
               "wait_timeout": 300, "max_text": 1000},
  "voice": "ずんだもん/ノーマル",
  "limits": {"speed": {"min": 0.5, "max": 2.0, "step": 0.01, "default": 1.0, "label": "速さ"}, ...}
}
```

| 項目 | 内容 |
|---|---|
| `settings` | 今の設定 |
| `voice` | `speaker` の名前（エンジンにつながらないときは `null`） |
| `limits` | 各項目の範囲と初期値 |

## PUT /settings

いつもの設定を変えます。変えたい項目だけ送れば、ほかはそのままです。変えた設定は `data/settings.json` に保存され、再起動しても残ります。

```bash
curl -X PUT http://localhost:8080/settings \
  -H "Content-Type: application/json" \
  -d '{"speaker":"四国めたん/あまあま","speed":1.2}'
```

| 項目 | 範囲 |
|---|---|
| `speaker` | 名前 / 名前/話し方 / 番号（`/speak` と同じ） |
| `speed` `pitch` `intonation` `volume` `pre_silence` `post_silence` `pause` | `/speak` と同じ |
| `wait_timeout` | 1〜3600（秒）。読み上げの終わりを待つ最大時間 |
| `max_text` | 1〜10000。`/speak` で 1 回に送れる文字数 |

返事は `GET /settings` と同じ形です。知らない項目や範囲外の値を送ると、何も変えずに `400` を返します。

## DELETE /settings

いつもの設定を初期値に戻します（`data/settings.json` を消します）。

```bash
curl -X DELETE http://localhost:8080/settings
```

## GET /health

```bash
curl http://localhost:8080/health
```

| ステータス | 本文の例 |
|---|---|
| `200` | `{"status": "ok", "engine": "0.25.2", "queue": 0}` |
| `503` | `{"status": "engine unreachable", "error": "..."}` |

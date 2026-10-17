# voicevox-server

HTTP でテキストを受け取り、このマシンのスピーカーから [VOICEVOX](https://voicevox.hiroshiba.jp/) でしゃべらせるサーバー。

📖 **ドキュメント: https://suke-toudara.github.io/voicevox-server/**

```
クライアント ──HTTP(8080)──▶ wrapper ──▶ VOICEVOX エンジン
                                              └──▶ PipeWire / PulseAudio ──▶ スピーカー
```

## クイックスタート

```bash
docker compose up -d --build    # エンジンと wrapper を起動
```

```bash
curl -X POST http://localhost:8080/speak \
  -H "Content-Type: application/json" \
  -d '{"text":"こんにちは"}'
```

止めるときは `docker compose down`。Docker なしで動かす場合は `./run.sh`（Ctrl+C で停止）。

## API

| メソッド | パス | 内容 |
|---|---|---|
| POST | `/speak` | しゃべらせる。読み上げが終わってから返す（`"wait": false` ですぐ返す） |
| GET | `/speakers` | 話者と話し方の一覧 |
| GET / PUT / DELETE | `/settings` | いつもの設定（声・速さなど）を見る / 変える / 初期値に戻す |
| GET | `/health` | 稼働確認 |
| GET | `/` | Web 画面（声や設定を変えられる） |

声は名前でも指定できる: `{"text":"こんにちは","speaker":"四国めたん/あまあま"}`

## 設定を変える

設定は 2 種類ある。

- **いつもの設定**（声・速さなど）: Web 画面か API で変える。再起動しても残る（`data/settings.json` に保存）
- **起動時の設定**（ポートなど）: `.env` に書いて起動し直す

### いつもの設定

`/speak` で項目を省略したときに使われる値。

**① Web 画面で変える**

ブラウザで `http://localhost:8080/` を開き、声やスライダーを変えて「保存」を押す。「読み上げる」ボタンで、保存する前に試し聞きできる。

**② API で変える**

変えたい項目だけ送れば、ほかはそのまま。

```bash
# 変える
curl -X PUT http://localhost:8080/settings \
  -H "Content-Type: application/json" \
  -d '{"speaker":"四国めたん/あまあま","speed":1.2}'

# 今の設定を見る
curl http://localhost:8080/settings

# 初期値に戻す
curl -X DELETE http://localhost:8080/settings
```

**③ 1 回だけ変える**

`/speak` に同じ項目を付けると、その 1 回だけその値で読み上げる（いつもの設定は変わらない）。

```bash
curl -X POST http://localhost:8080/speak \
  -H "Content-Type: application/json" \
  -d '{"text":"今回だけ速く","speaker":"ずんだもん/ささやき","speed":1.5}'
```

| 項目 | 内容 | 範囲 | 初期値 | `/speak` で 1 回だけ変える |
|---|---|---|---|---|
| `speaker` | 声。`"名前"` / `"名前/話し方"` / 番号 | `/speakers` で確認 | `3`（ずんだもん/ノーマル） | ○ |
| `speed` | 速さ | 0.5〜2.0 | 1.0 | ○ |
| `pitch` | 高さ | -0.15〜0.15 | 0.0 | ○ |
| `intonation` | 抑揚 | 0〜2.0 | 1.0 | ○ |
| `volume` | 音量 | 0〜2.0 | 1.0 | ○ |
| `pre_silence` | 開始前の無音（秒） | 0〜1.5 | 0.1 | ○ |
| `post_silence` | 終了後の無音（秒） | 0〜1.5 | 0.1 | ○ |
| `pause` | 句読点の長さ（倍率） | 0〜2.0 | 1.0 | ○ |
| `wait_timeout` | 読み上げの終わりを待つ最大秒数 | 1〜3600 | 300 | × |
| `max_text` | 1 回に読み上げられる最大文字数 | 1〜10000 | 1000 | × |

範囲外の値や知らない項目を送ると、何も変えずに `400` を返す。

### 起動時の設定（.env）

リポジトリの直下に `.env` を作って、必要な行だけ書く（`.env` が無くても動く）。書いたら起動し直す。

```bash
# .env の例
VV_PORT=9000
VV_SPEAKER=四国めたん
```

```bash
docker compose up -d   # 起動し直すと反映される
```

| 変数 | 初期値 | 内容 |
|---|---|---|
| `VV_PORT` | `8080` | 待ち受けポート |
| `VV_SPEAKER` | `3` | いつもの声の初期値（番号か名前）。画面や API で保存した値があればそちらが優先 |
| `VV_WAIT_TIMEOUT` | `300` | `wait_timeout` の初期値 |
| `VV_PLAYER` | `pw-play`（Docker では `paplay`） | 再生コマンド |
| `VV_TOKEN` | なし | 合言葉。設定すると `Authorization: Bearer <合言葉>` ヘッダが必要になる |
| `VV_ENGINE_IMAGE` | `voicevox/voicevox_engine:cpu-latest` | エンジンの Docker イメージ |

ほかの項目や詳しい説明は[ドキュメント](https://suke-toudara.github.io/voicevox-server/)を参照。

## ドキュメントをローカルで見る

```bash
mdbook serve docs --open
```

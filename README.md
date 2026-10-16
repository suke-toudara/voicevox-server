# voicevox-https-wrapper

HTTPS でテキストを受け取り、このマシンのスピーカーから [VOICEVOX](https://voicevox.hiroshiba.jp/) でしゃべらせるラッパー。

```
クライアント ──HTTPS(8443, トークン認証)──▶ server.py ──▶ VOICEVOX エンジン (Docker, 127.0.0.1:50021)
                                              └──▶ pw-play ──▶ スピーカー
```

- Python 標準ライブラリのみ（追加インストール不要）
- 連続で送られても順番に再生（キュー）
- エンジンは 127.0.0.1 のみで待ち受け、外部からはラッパー経由でしか使えない

## 必要なもの

- Docker
- Python 3.10+
- `pw-play`（PipeWire）。別のプレイヤーを使う場合は `VV_PLAYER=aplay` などを指定

## セットアップ

```bash
cp .env.example .env
sed -i "s/change-me/$(openssl rand -hex 16)/" .env
./gen-cert.sh   # 自己署名証明書を作成（run.sh 初回実行時にも自動で作られる）
```

## 起動

```bash
./run.sh
```

エンジンのコンテナを起動してからラッパーをフォアグラウンドで動かす。Ctrl+C でラッパーとエンジンの両方が止まる。

## API

| メソッド | パス | 認証 | 内容 |
|---|---|---|---|
| POST | `/speak` | 要 | しゃべらせる（JSON / フォーム / 生テキスト） |
| GET | `/speak?text=...` | 要 | 同上（URL だけで呼べる） |
| GET | `/speakers` | 要 | 話者とスタイル ID の一覧 |
| GET | `/health` | 不要 | ラッパーとエンジンの稼働確認 |

認証は `Authorization: Bearer <token>` ヘッダか `?token=<token>`。

`/speak` のパラメータ: `text`（必須, 1000 文字まで）, `speaker`（スタイル ID）, `speed`, `pitch`, `intonation`, `volume`

```bash
TOKEN=...   # .env の VV_TOKEN

curl -k -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"text":"こんにちは","speaker":3,"speed":1.2}' https://<host>:8443/speak

curl -k "https://<host>:8443/speak?token=$TOKEN&text=テスト"
```

## 設定（.env）

| 変数 | 既定値 | 内容 |
|---|---|---|
| `VV_TOKEN` | （空=認証なし） | クライアント用トークン |
| `VV_PORT` | `8443` | 待ち受けポート |
| `VV_HOST` | `0.0.0.0` | 待ち受けアドレス |
| `VV_SPEAKER` | `3`（ずんだもん ノーマル） | 既定の話者 |
| `VV_PLAYER` | `pw-play` | 再生コマンド |
| `VV_CERT` / `VV_KEY` | `certs/server.crt` / `certs/server.key` | 証明書。無ければ HTTP で起動 |
| `VV_ENGINE` | `http://127.0.0.1:50021` | エンジンの URL |
| `VV_ENGINE_IMAGE` | `voicevox/voicevox_engine:cpu-latest` | run.sh が使うエンジンイメージ |

## 証明書について

自己署名なので curl では `-k` が必要。検証したい場合は `certs/server.crt` をクライアントに配って `--cacert server.crt` を使う。

# トラブルシューティング

## 202 が返るのに声が出ない

ログにエラーが出ていないか確認します。

```bash
docker compose logs wrapper     # Docker の場合
```

`[error] ...` と出ていれば、その内容が原因です。よくある原因は次のとおりです。

- **デスクトップにログインしていない**: 音声サーバーはログイン中のユーザーのものなので、ログインしていないと音が出ません
- **音声ソケットが見つからない**: `ls $XDG_RUNTIME_DIR/pulse/native` でファイルがあるか確認します。無い場合は PipeWire（`pipewire-pulse`）か PulseAudio が動いていません
- **ユーザー ID が違う**: ユーザー ID が 1000 以外なら `UID=$(id -u) GID=$(id -g) docker compose up -d` で起動します
- **音量やミュート**: PC 側の出力先や音量を確認します

コンテナから音声サーバーにつながるかは、次のコマンドで確かめられます。

```bash
docker compose exec wrapper pactl info
```

`Server String: unix:/run/pulse/native` と出れば、つながっています。

## 401 unauthorized

`.env` で `VV_TOKEN`（合言葉）を設定しているときだけ出ます。

- `Authorization: Bearer <合言葉>` ヘッダが付いているか確認します
- 合言葉が `.env` の `VV_TOKEN` と同じか確認します
- 合言葉が不要なら、`.env` から `VV_TOKEN` の行を消して起動し直します

## 405 use POST /speak

`GET` で `/speak` を呼んでいます。`POST` で呼んでください。

## 503 engine unreachable

VOICEVOX エンジンが起動していないか、まだ準備中です。起動直後は数秒〜数十秒待ってください。

```bash
docker compose ps
docker compose logs voicevox
```

## 別の PC からつながらない

- `curl -k https://<IP>:8443/health` が返るか確認します
- ファイアウォールでポートを開けます（ufw の場合: `sudo ufw allow 8443/tcp`）
- 同じネットワークにいるか確認します

## curl: (60) SSL certificate problem

自己署名証明書を使っているときに出ます。`-k` を付けるか、`--cacert server.crt` で証明書を渡してください。詳しくは [簡易：自己署名証明書](https-self-signed.md) を見てください。

## curl: (35) / wrong version number

HTTPS で HTTP のサーバーにつないでいます。`certs/server.crt` と `certs/server.key` が無いと、wrapper は HTTP で起動します。`./gen-cert.sh` で証明書を作ってから起動し直してください。

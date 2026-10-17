# 設定

設定は `.env` ファイルに書きます。見本は `.env.example` です。

| 変数 | 既定値 | 内容 |
|---|---|---|
| `VV_TOKEN` | （空 = 認証なし） | クライアント用の合言葉。必ず設定してください |
| `VV_PORT` | `8443` | 待ち受けポート |
| `VV_SPEAKER` | `3`（ずんだもん ノーマル） | `speaker` を省略したときの声 |
| `VV_PLAYER` | `pw-play`（Docker では `paplay`） | 再生コマンド |
| `VV_HOST` | `0.0.0.0` | 待ち受けアドレス |
| `VV_CERT` / `VV_KEY` | `certs/server.crt` / `certs/server.key` | 証明書と秘密鍵。無ければ HTTP で起動します |
| `VV_ENGINE` | `http://127.0.0.1:50021` | VOICEVOX エンジンの URL |
| `VV_ENGINE_IMAGE` | `voicevox/voicevox_engine:cpu-latest` | エンジンの Docker イメージ |

設定を変えたら、起動し直すと反映されます。

```bash
docker compose up -d   # Docker の場合
```

## GPU 版のエンジンを使う

NVIDIA GPU がある場合は、イメージを GPU 版に変えると音声の生成が速くなります。

```bash
# .env
VV_ENGINE_IMAGE=voicevox/voicevox_engine:nvidia-latest
```

GPU をコンテナから使うには、`compose.yaml` の `voicevox` サービスに GPU の割り当てを追加し、ホストに NVIDIA Container Toolkit を入れる必要があります。

```yaml
  voicevox:
    image: ${VV_ENGINE_IMAGE:-voicevox/voicevox_engine:cpu-latest}
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
```

## Docker で音を出すしくみ

wrapper のコンテナは、ホストの音声サーバー（PipeWire / PulseAudio）のソケットを共有して音を出します。`compose.yaml` では次の設定がそれにあたります。

```yaml
    user: "${UID:-1000}:${GID:-1000}"
    volumes:
      - ${XDG_RUNTIME_DIR:-/run/user/1000}/pulse/native:/run/pulse/native
    environment:
      PULSE_SERVER: unix:/run/pulse/native
```

- ソケットはデスクトップにログインしているユーザーのものなので、コンテナも同じユーザー ID で動かします
- ユーザー ID が 1000 以外の場合は、`UID=$(id -u) GID=$(id -g) docker compose up -d` のように指定してください

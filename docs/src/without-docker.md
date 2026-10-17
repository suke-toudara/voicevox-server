# Docker なしで動かす

wrapper をホストの Python で直接動かす方法です。VOICEVOX エンジンだけは Docker で動かします。

## 必要なもの

- Docker（エンジン用）
- Python 3.10 以上
- `pw-play`（PipeWire）。無い場合は `.env` に `VV_PLAYER=aplay` などを指定します

## 起動

証明書の作り方は [クイックスタート](quickstart.md) の 2 と同じです。

```bash
./run.sh
```

`run.sh` は次のことを順番に行います。

1. 証明書が無ければ `gen-cert.sh` で作る
2. VOICEVOX エンジンのコンテナを起動する（`127.0.0.1:50021`）
3. エンジンの準備ができるまで待つ
4. wrapper をフォアグラウンドで起動する

`listening on https://0.0.0.0:8443 ...` と出たら準備完了です。

## 止める

`run.sh` を動かしているターミナルで **Ctrl + C** を押します。エンジンのコンテナも一緒に止まります。

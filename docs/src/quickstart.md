# クイックスタート（Docker）

`docker compose` で、VOICEVOX エンジンと wrapper の 2 つをまとめて起動します。

## 必要なもの

- Docker と Docker Compose
- Linux デスクトップ（PipeWire または PulseAudio で音が出ていること）

## 1. 取ってくる

```bash
git clone https://github.com/suke-toudara/voicevox-server.git
cd voicevox-server
```

## 2. 起動する

```bash
docker compose up -d --build
```

初回はイメージのダウンロードがあるので少し時間がかかります。起動できたか確認します。

```bash
curl http://localhost:8080/health
# {"status": "ok", "engine": "0.25.2", "queue": 0}
```

## 3. しゃべらせる

```bash
curl -X POST http://localhost:8080/speak \
  -H "Content-Type: application/json" \
  -d '{"text":"こんにちは"}'
```

スピーカーから声が聞こえれば成功です。別の PC から呼ぶときは `localhost` をこのマシンの IP アドレスに変えます。

ブラウザで `http://localhost:8080/` を開くと、声や設定を変えられる [Web 画面](ui.md) が使えます。

## 4. 止める

```bash
docker compose down
```

自動起動の設定はしていないので、PC を再起動したあとは `docker compose up -d` で起動し直します。

## 設定を変えたいとき

声の種類やポートを変えたいときは、`.env` を作って書きます。何も書かなければ既定値で動きます。

```bash
vim .env
```
```bash
#VV_TOKEN=
```
書ける項目は [設定](configuration.md) を見てください。

## ログを見る

```bash
docker compose logs -f wrapper
```

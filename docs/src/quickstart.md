# クイックスタート（Docker）

`docker compose` で、VOICEVOX エンジンと wrapper の 2 つをまとめて起動します。

## 必要なもの

- Docker と Docker Compose
- Linux デスクトップ（PipeWire または PulseAudio で音が出ていること）
- `openssl`（証明書を作るのに使います）

## 1. 取ってくる

```bash
git clone https://github.com/suke-toudara/voicevox-https-wrapper.git
cd voicevox-https-wrapper
```

## 2. 証明書を作る

```bash
./gen-cert.sh
```

`certs/` フォルダに、このマシンの名前と IP アドレスが入った自己署名証明書ができます。証明書について詳しくは [HTTPS と証明書](https.md) を見てください。

## 3. 起動する

```bash
docker compose up -d --build
```

初回はイメージのダウンロードがあるので少し時間がかかります。起動できたか確認します。

```bash
curl -k https://localhost:8443/health
# {"status": "ok", "engine": "0.25.2", "queue": 0}
```

## 4. しゃべらせる

```bash
curl -k -X POST https://localhost:8443/speak \
  -H "Content-Type: application/json" \
  -d '{"text":"こんにちは"}'
```

スピーカーから声が聞こえれば成功です。別の PC から呼ぶときは `localhost` をこのマシンの IP アドレスに変えます。

## 5. 止める

```bash
docker compose down
```

自動起動の設定はしていないので、PC を再起動したあとは `docker compose up -d` で起動し直します。

## 設定を変えたいとき

声の種類やポートを変えたいときは、`.env` を作って書きます。何も書かなければ既定値で動きます。

```bash
cp .env.example .env
```

書ける項目は [設定](configuration.md) を見てください。

## ログを見る

```bash
docker compose logs -f wrapper
```

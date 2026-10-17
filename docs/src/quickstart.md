# クイックスタート（Docker）

`docker compose` で、VOICEVOX エンジンと wrapper の 2 つをまとめて起動します。

## 必要なもの

- Docker と Docker Compose
- Linux デスクトップ（PipeWire または PulseAudio で音が出ていること）
- `openssl`（証明書と合言葉を作るのに使います）

## 1. 取ってくる

```bash
git clone https://github.com/suke-toudara/voicevox-https-wrapper.git
cd voicevox-https-wrapper
```

## 2. 合言葉（トークン）を作る

```bash
cp .env.example .env
sed -i "s/change-me/$(openssl rand -hex 16)/" .env
cat .env
```

`VV_TOKEN=` の後ろに出てきた英数字が合言葉です。呼び出すときに使うので控えておきます。

> `openssl rand -hex 16` は「ランダムな英数字を 32 文字作って」という命令です。

## 3. 証明書を作る

```bash
./gen-cert.sh
```

`certs/` フォルダに、このマシンの名前と IP アドレスが入った自己署名証明書ができます。証明書について詳しくは [HTTPS と証明書](https.md) を見てください。

## 4. 起動する

```bash
docker compose up -d --build
```

初回はイメージのダウンロードがあるので少し時間がかかります。起動できたか確認します。

```bash
curl -k https://localhost:8443/health
# {"status": "ok", "engine": "0.25.2", "queue": 0}
```

## 5. しゃべらせる

```bash
TOKEN=控えた合言葉

curl -k -X POST https://localhost:8443/speak \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"こんにちは"}'
```

スピーカーから声が聞こえれば成功です。別の PC から呼ぶときは `localhost` をこのマシンの IP アドレスに変えます。

## 6. 止める

```bash
docker compose down
```

自動起動の設定はしていないので、PC を再起動したあとは `docker compose up -d` で起動し直します。

## ログを見る

```bash
docker compose logs -f wrapper
```

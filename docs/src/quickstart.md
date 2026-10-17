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

**声・速さなど** は、ブラウザで `http://localhost:8080/` を開いて変えます（[Web 画面](ui.md)）。保存すれば再起動しても残ります。

**ポートや合言葉など** は、リポジトリの直下に `.env` というファイルを作って、変えたい行だけ書きます。何も書かなければ既定値で動きます。

```bash
# .env の例
VV_PORT=9000            # 待ち受けポートを 9000 番にする
VV_TOKEN=himitsu        # 合言葉を付ける（付けない場合はこの行を書かない）
```

書いたら起動し直すと反映されます。

```bash
docker compose up -d
```

書ける項目は [設定](configuration.md) を見てください。

## ログを見る

```bash
docker compose logs -f wrapper
```

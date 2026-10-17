# voicevox-https-wrapper

HTTP でテキストを受け取り、このマシンのスピーカーから [VOICEVOX](https://voicevox.hiroshiba.jp/) でしゃべらせるラッパー。

📖 **ドキュメント: https://suke-toudara.github.io/voicevox-https-wrapper/**

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
| GET | `/speakers` | 話者とスタイル ID の一覧 |
| GET | `/health` | 稼働確認 |

設定は `.env.example` を `.env` にコピーして書く（無くても動く）。詳しくは[ドキュメント](https://suke-toudara.github.io/voicevox-https-wrapper/)を参照。

## ドキュメントをローカルで見る

```bash
mdbook serve docs --open
```

# voicevox-https-wrapper

HTTPS でテキストを受け取り、このマシンのスピーカーから [VOICEVOX](https://voicevox.hiroshiba.jp/) でしゃべらせるラッパー。

📖 **ドキュメント: https://suke-toudara.github.io/voicevox-https-wrapper/**

```
クライアント ──HTTPS(8443, トークン認証)──▶ wrapper ──▶ VOICEVOX エンジン
                                              └──▶ PipeWire / PulseAudio ──▶ スピーカー
```

## クイックスタート

```bash
cp .env.example .env
sed -i "s/change-me/$(openssl rand -hex 16)/" .env   # 合言葉を作る
./gen-cert.sh                                        # 自己署名証明書を作る
docker compose up -d --build                         # エンジンと wrapper を起動
```

```bash
curl -k -X POST https://localhost:8443/speak \
  -H "Authorization: Bearer $(grep VV_TOKEN .env | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d '{"text":"こんにちは"}'
```

止めるときは `docker compose down`。Docker なしで動かす場合は `./run.sh`（Ctrl+C で停止）。

## API

| メソッド | パス | 認証 | 内容 |
|---|---|---|---|
| POST | `/speak` | 要 | しゃべらせる（JSON / フォーム / テキスト） |
| GET | `/speakers` | 要 | 話者とスタイル ID の一覧 |
| GET | `/health` | 不要 | 稼働確認 |

認証は `Authorization: Bearer <token>` ヘッダ。詳しくは[ドキュメント](https://suke-toudara.github.io/voicevox-https-wrapper/)を参照。

## ドキュメントをローカルで見る

```bash
mdbook serve docs --open
```

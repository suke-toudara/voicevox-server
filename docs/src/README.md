# はじめに

**voicevox-https-wrapper** は、HTTPS で送られてきたテキストを、サーバーを動かしているマシンのスピーカーから [VOICEVOX](https://voicevox.hiroshiba.jp/) の声で読み上げるラッパーです。

```bash
curl -k -X POST https://<host>:8443/speak \
  -H "Content-Type: application/json" \
  -d '{"text":"こんにちは"}'
```

これだけで、サーバーのスピーカーから「こんにちは」と聞こえます。

## しくみ

```text
クライアント ──HTTPS(8443)──▶ wrapper ──▶ VOICEVOX エンジン
                                              │
                                              └──▶ PipeWire / PulseAudio ──▶ スピーカー
```

- **wrapper**: テキストを受け取り、エンジンで音声を作って再生します。Python 標準ライブラリだけで書かれています
- **VOICEVOX エンジン**: テキストから音声（WAV）を作ります。外からは直接触れず、wrapper からしか使えません
- **キュー**: 続けて送られても声が重ならないよう、1 つずつ順番に再生します

## 使いどころ

- 長い処理やビルドが終わったら声で知らせる
- ロボットや IoT 機器から、PC に状況を読み上げさせる
- LAN 内の別の PC やスマホから、この PC にしゃべらせる

まずは [クイックスタート](quickstart.md) から始めてください。

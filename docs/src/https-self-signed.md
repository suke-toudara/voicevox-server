# 簡易：自己署名証明書

自分でハンコを押した証明書です。`gen-cert.sh` を実行すると作れます。

```bash
./gen-cert.sh
```

## gen-cert.sh がやっていること

中身は次のコマンド 1 つです。これで「秘密鍵を作る → 名札を書く → 自分でハンコを押す」が全部終わります。

```bash
openssl req -x509 -newkey rsa:2048 -nodes -days 3650 \
  -keyout certs/server.key -out certs/server.crt \
  -subj "/CN=mypc" \
  -addext "subjectAltName=DNS:mypc,DNS:localhost,IP:127.0.0.1,IP:192.168.0.10"
```

| 部分 | 意味 |
|---|---|
| `openssl req` | 証明書を作る道具を使う |
| `-newkey rsa:2048` | 新しい秘密鍵（ハンコ）を作る。2048 は強さ |
| `-nodes` | 秘密鍵にパスワードをかけない（サーバーが自動で読めるように） |
| `-x509` | 認証局に頼まず、**自分でハンコを押して** 完成させる。これが「自己署名」 |
| `-days 3650` | 有効期限は 3650 日（約 10 年） |
| `-keyout` | 秘密鍵を保存するファイル |
| `-out` | 証明書を保存するファイル |
| `-subj "/CN=mypc"` | 名札に書く名前 |
| `-addext "subjectAltName=..."` | 「この名前や IP で呼ばれたら私です」というリスト。ブラウザは主にここを見る |

`gen-cert.sh` は、マシンの名前と IP アドレスを自動で調べて `subjectAltName` に入れます。IP アドレスが変わったら、もう一度実行して作り直してください。

## 中身を見る

```bash
openssl x509 -in certs/server.crt -noout -text | less
```

`Issuer`（ハンコを押した人）と `Subject`（名札の持ち主）が同じになっています。これが「自分で押した」印です。

## 警告が出る理由

自分で押したハンコは、ほかの人から見ると本物かどうか分かりません。そのため、ブラウザやプログラムは「信用できない」と警告します。

- **curl**: `-k` を付けると「分かってるから送って」という意味になり、確認を省きます
- **ブラウザ**: 警告画面で「詳細」→「アクセスする」を選びます

## クライアントに証明書を信用させる

`-k` を使わずに、ちゃんと確認させることもできます。`certs/server.crt` をクライアントにコピーして、「この名札は信用していい」と教えます。

```bash
# curl
curl --cacert server.crt -X POST https://192.168.0.10:8443/speak ...

# Python requests
requests.post(..., verify="server.crt")
```

この方法なら、ニセモノのサーバーにつながったときに気づけます。`server.crt` は配っても大丈夫ですが、`server.key` は絶対に配らないでください。

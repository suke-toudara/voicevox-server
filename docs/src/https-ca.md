# 正式：認証局の証明書

みんなが信用している **認証局**（先生）にハンコを押してもらった証明書です。警告が出ず、`-k` も要りません。

## しくみ

1. 秘密鍵を作る（自分で）
2. **CSR（証明書署名要求）** を作る。「この名前の名札にハンコをください」という申請書です
3. 認証局が「本当にこの名前の持ち主か」を確かめる
4. 確かめられたら、ハンコを押した証明書が返ってくる

手作業でやるとこうなります（実際には、下で紹介するツールがすべて自動でやってくれます）。

```bash
# 1. 秘密鍵を作る
openssl genrsa -out server.key 2048
# 2. 申請書（CSR）を作る
openssl req -new -key server.key -out server.csr -subj "/CN=example.com"
# 3〜4. server.csr を認証局に出す → 確認 → server.crt が返ってくる
```

## 大事な条件：ドメイン名が必要

認証局は「`example.com` の持ち主ですか？」を確かめます。そのため **自分のドメイン名** が必要です。`192.168.0.10` のような LAN の中の IP アドレスには、正式な証明書は出してもらえません。

確かめ方は 2 通りあります。

- **HTTP 認証**: 認証局が `http://example.com/...` にアクセスして、指定された合言葉のファイルが置いてあるか見る。インターネットから自分のマシンに届く必要がある
- **DNS 認証**: ドメインの設定（DNS）に、指定された合言葉を書き込む。マシンが外から見えなくてもいい

## 方法 A：Tailscale（いちばん簡単）

[Tailscale](https://tailscale.com/) を使っていれば、マシンには `mypc.tailXXXX.ts.net` のような名前が付いています。Tailscale は、この名前の正式な証明書（Let's Encrypt 製）を代わりに取ってきてくれます。ドメインを買う必要はありません。

1. Tailscale の管理画面の [DNS 設定](https://login.tailscale.com/admin/dns) で **MagicDNS** と **HTTPS Certificates** を有効にする
2. マシンの名前を調べる

   ```bash
   tailscale status --self --json | grep DNSName
   ```

3. 証明書を取ってくる

   ```bash
   sudo tailscale cert \
     --cert-file certs/server.crt --key-file certs/server.key \
     mypc.tailXXXX.ts.net
   sudo chown $USER certs/server.*
   ```

4. 起動し直して、Tailscale につながっている端末から呼ぶ

   ```bash
   curl -X POST https://mypc.tailXXXX.ts.net:8443/speak ...
   ```

`-k` なしで通ります。ただし使えるのは、同じ Tailscale ネットワークに入っている端末からだけです。証明書の期限は 90 日なので、期限が近づいたら 3 をもう一度実行します。

## 方法 B：Let's Encrypt（自分のドメインがある場合）

[Let's Encrypt](https://letsencrypt.org/ja/) は無料の認証局です。`certbot` というツールで証明書を取ります。

```bash
sudo apt install certbot

# HTTP 認証（80 番ポートがインターネットから届く場合）
sudo certbot certonly --standalone -d example.com

# DNS 認証（LAN の中のマシンの場合）
sudo certbot certonly --manual --preferred-challenges dns -d example.com
```

できたファイルは `/etc/letsencrypt/live/example.com/` に入ります。

| ファイル | 中身 | 指定先 |
|---|---|---|
| `fullchain.pem` | 証明書 | `VV_CERT` |
| `privkey.pem` | 秘密鍵 | `VV_KEY` |

Docker で使う場合は、この 2 つを `certs/server.crt` と `certs/server.key` という名前でコピーするのが簡単です。

```bash
sudo cp /etc/letsencrypt/live/example.com/fullchain.pem certs/server.crt
sudo cp /etc/letsencrypt/live/example.com/privkey.pem certs/server.key
sudo chown $USER certs/server.*
```

有効期限は 90 日なので、`sudo certbot renew` で更新し、もう一度コピーして起動し直します。

# エンジニア ポートフォリオ

チームのエンジニアのスキルと制作物を一覧で見られるサイト。Next.js の静的書き出しで、
メンバー情報は1人1ファイルのJSONで管理する。DBやログインは不要。

## メンバーを追加・更新する

1. `content/members/_TEMPLATE.json` をコピーして `content/members/<自分のID>.json` を作る
   - ファイル名がURLになる（`taro-yamada.json` → `/members/taro-yamada/`）。半角英小文字・数字・ハイフンのみ
2. 中身を書き換える。`name` と、制作物を載せる場合はその `title` だけが必須。使わない項目は消してよい
3. 顔写真を載せる場合は `public/avatars/` に画像を置き、`"avatar": "/avatars/taro-yamada.png"` と書く。
   なければ名前の頭文字のアイコンになる
4. プルリクエストを送る。CIがビルドして、書き間違い（URLの形式、必須項目の欠落など）があれば
   どのファイルのどの項目かをエラーで知らせる

| 項目 | 内容 |
| --- | --- |
| `name` | 表示名（必須） |
| `nameKana` | 読み。一覧の並び順に使う |
| `role` | 役割（例: バックエンド） |
| `bio` | 自己紹介 |
| `skills` | スキルの配列。一覧の絞り込みタグになる |
| `links` | `github` / `x` / `site` / `zenn` / `qiita` のURL |
| `projects` | 制作物の配列。`title` `description` `url` `repo` `tech` `year` |
| `joinedAt` | 入社・参加時期（例: `2024-04`） |

## 手元で動かす

```bash
cd team-portfolio
npm install
npm run dev        # http://localhost:3000
npm run build      # out/ に静的サイトを書き出す
```

## 独自ドメインで公開する（Vercel の場合）

1. https://vercel.com で GitHub アカウントを連携し、「Add New → Project」からこのリポジトリを選ぶ
2. **Root Directory** に `team-portfolio` を指定する（Framework は Next.js が自動で選ばれる）
3. **Environment Variables** に次を追加して Deploy
   - `NEXT_PUBLIC_SITE_URL` = `https://portfolio.example.com`（公開するURL）
   - `NEXT_PUBLIC_TEAM_NAME` = チーム名（ヘッダーとページタイトルに出る）
4. プロジェクトの **Settings → Domains** で独自ドメインを追加する
5. Vercel の画面に表示されるDNSレコードを、ドメインを買ったサービス（お名前.com、Cloudflare など）で設定する
   - サブドメイン（`portfolio.example.com`）なら CNAME レコード
   - ルートドメイン（`example.com`）なら A レコード
6. 反映されると HTTPS 証明書は自動で発行される。以降は main にマージするたびに自動で再公開される

Cloudflare Pages / Netlify を使う場合も、ルートを `team-portfolio`、ビルドコマンドを `npm run build`、
公開ディレクトリを `out` にすれば同じように動く。

## 社内だけに公開したい場合

このサイトは誰でも見られる静的サイトになる。社内限定にしたい場合は、配信側でアクセス制限をかける
（Vercel の Deployment Protection、Cloudflare Access など）。

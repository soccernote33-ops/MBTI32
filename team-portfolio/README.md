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

## 公開のしくみ（GitHub Pages）

`team-portfolio/` 以下が変わってpushされると、GitHub Actions（`.github/workflows/team-portfolio.yml`）が
サイトをビルドし、`gh-pages` ブランチに書き出す。GitHub Pages がそのブランチを配信する。

- 公開URL: https://soccernote33-ops.github.io/MBTI32/
- プルリクエストではビルドの確認だけを行い、公開はしない
- 初回だけ、リポジトリの **Settings → Pages** で Source を「Deploy from a branch」、
  Branch を `gh-pages` / `/(root)` にする

### 独自ドメインに切り替える

1. ドメインを取得する（お名前.com、Cloudflare Registrar など）
2. ドメイン管理画面のDNSに、次のどちらかを追加する
   - サブドメイン（`portfolio.example.com`）: CNAME レコード → `soccernote33-ops.github.io`
   - ルートドメイン（`example.com`）: A レコード → `185.199.108.153` `185.199.109.153` `185.199.110.153` `185.199.111.153`
3. `.github/workflows/team-portfolio.yml` の `env` を書き換えてpushする
   - `CUSTOM_DOMAIN`: `portfolio.example.com`
   - `NEXT_PUBLIC_SITE_URL`: `https://portfolio.example.com`
   - `NEXT_PUBLIC_BASE_PATH`: `""`（空にする）
4. **Settings → Pages** にドメインが表示されたら「Enforce HTTPS」にチェックを入れる

## 社内だけに公開したい場合

GitHub Pages で公開したサイトは誰でも見られる。社内限定にしたい場合は、Vercel（Deployment Protection）や
Cloudflare Pages（Cloudflare Access）に移す。どちらもルートを `team-portfolio`、ビルドコマンドを `npm run build`、
公開ディレクトリを `out` にすれば動く。

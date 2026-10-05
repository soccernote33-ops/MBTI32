// チーム名やURLは環境変数で渡す (.github/workflows/team-portfolio.yml の env)
export const site = {
  teamName: process.env.NEXT_PUBLIC_TEAM_NAME ?? "Engineering Team",
  title: "エンジニア ポートフォリオ",
  description: "チームのエンジニアのスキルと制作物の一覧",
  url: process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000",
};

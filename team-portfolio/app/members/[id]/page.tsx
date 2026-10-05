import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Avatar } from "@/components/Avatar";
import { getMember, getMembers } from "@/lib/members";

type Props = { params: Promise<{ id: string }> };

export const dynamicParams = false;

// 静的書き出しは最低1ページを要求するので、メンバー0人のときは 404 になるダミーを1つ出す
const EMPTY_PLACEHOLDER = "_";

export function generateStaticParams() {
  const ids = getMembers().map((m) => ({ id: m.id }));
  return ids.length ? ids : [{ id: EMPTY_PLACEHOLDER }];
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const m = getMember((await params).id);
  if (!m) return {};
  return { title: m.name, description: m.bio ?? m.role };
}

const LINK_LABELS: Record<string, string> = { github: "GitHub", x: "X", site: "Website", zenn: "Zenn", qiita: "Qiita" };

export default async function MemberPage({ params }: Props) {
  const m = getMember((await params).id);
  if (!m) notFound();

  const links = Object.entries(m.links).filter((e): e is [string, string] => !!e[1]);

  return (
    <main className="stack">
      <Link href="/" className="back">← 一覧へ</Link>

      <header className="profile">
        <Avatar member={m} size={88} />
        <div className="profile-text">
          {m.nameKana && <div className="eyebrow">{m.nameKana}</div>}
          <h1>{m.name}</h1>
          {m.role && <div className="role">{m.role}</div>}
        </div>
      </header>

      {m.bio && <p className="bio">{m.bio}</p>}

      {m.skills.length > 0 && (
        <section className="stack-sm">
          <h2 className="label">Skills</h2>
          <div className="chips">
            {m.skills.map((s) => <span key={s} className="chip">{s}</span>)}
          </div>
        </section>
      )}

      {links.length > 0 && (
        <section className="stack-sm">
          <h2 className="label">Links</h2>
          <div className="links">
            {links.map(([k, href]) => (
              <a key={k} href={href} target="_blank" rel="noopener noreferrer">{LINK_LABELS[k] ?? k} ↗</a>
            ))}
          </div>
        </section>
      )}

      <section className="stack-sm">
        <h2 className="label">Projects ({m.projects.length})</h2>
        {m.projects.length === 0 ? (
          <p className="muted">制作物はまだ登録されていません。</p>
        ) : (
          <div className="projects">
            {m.projects.map((p, i) => (
              <article key={i} className="proj">
                <div className="proj-head">
                  <h3>{p.title}</h3>
                  {p.year && <span className="year">{p.year}</span>}
                </div>
                {p.description && <p>{p.description}</p>}
                {p.tech && p.tech.length > 0 && (
                  <div className="chips">{p.tech.map((t) => <span key={t} className="chip">{t}</span>)}</div>
                )}
                {(p.url || p.repo) && (
                  <div className="links">
                    {p.url && <a href={p.url} target="_blank" rel="noopener noreferrer">デモ ↗</a>}
                    {p.repo && <a href={p.repo} target="_blank" rel="noopener noreferrer">リポジトリ ↗</a>}
                  </div>
                )}
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}

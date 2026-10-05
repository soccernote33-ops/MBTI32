"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import type { Member } from "@/lib/members";
import { Avatar } from "./Avatar";

export function MemberDirectory({ members }: { members: Member[] }) {
  const [query, setQuery] = useState("");
  const [tag, setTag] = useState<string | null>(null);

  const tags = useMemo(() => {
    const counts = new Map<string, number>();
    for (const m of members) for (const s of m.skills) counts.set(s, (counts.get(s) ?? 0) + 1);
    return [...counts].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).slice(0, 30);
  }, [members]);

  const shown = useMemo(() => {
    const q = query.trim().toLowerCase();
    return members.filter((m) => {
      if (tag && !m.skills.includes(tag)) return false;
      if (!q) return true;
      const hay = [m.name, m.nameKana, m.role, m.bio, ...m.skills, ...m.projects.flatMap((p) => [p.title, p.description, ...(p.tech ?? [])])]
        .join(" ")
        .toLowerCase();
      return hay.includes(q);
    });
  }, [members, query, tag]);

  if (members.length === 0) {
    return (
      <div className="empty">
        <h2>まだ誰も登録されていません</h2>
        <p>
          <code>content/members/_TEMPLATE.json</code> をコピーして自分の名前のファイルを作り、プルリクエストを送ると、ここにカードが並びます。
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="toolbar">
        <input
          id="q"
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="名前・技術・プロジェクト名で検索"
          aria-label="検索"
        />
      </div>
      {tags.length > 0 && (
        <div className="chips" aria-label="技術で絞り込み">
          {tags.map(([t, n]) => (
            <button key={t} type="button" className="chip" aria-pressed={t === tag} onClick={() => setTag(t === tag ? null : t)}>
              {t} <span className="chip-n">{n}</span>
            </button>
          ))}
        </div>
      )}
      {shown.length === 0 ? (
        <div className="empty">
          <h2>条件に合うメンバーがいません</h2>
          <p>検索語や技術タグを外してみてください。</p>
        </div>
      ) : (
        <ul className="grid">
          {shown.map((m) => (
            <li key={m.id}>
              <Link href={`/members/${m.id}/`} className="card">
                <div className="who">
                  <Avatar member={m} />
                  <div>
                    <h2>{m.name}</h2>
                    {m.role && <div className="role">{m.role}</div>}
                  </div>
                </div>
                {m.bio && <p className="bio-clamp">{m.bio}</p>}
                <div className="chips">
                  {m.skills.slice(0, 5).map((s) => (
                    <span key={s} className="chip">{s}</span>
                  ))}
                </div>
                <div className="meta">
                  <span>制作物 {m.projects.length}</span>
                  {m.joinedAt && <span>since {m.joinedAt}</span>}
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}

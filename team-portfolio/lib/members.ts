import fs from "node:fs";
import path from "node:path";

export type Project = {
  title: string;
  description?: string;
  url?: string;
  repo?: string;
  tech?: string[];
  year?: number;
};

export type Member = {
  id: string;
  name: string;
  nameKana?: string;
  role?: string;
  bio?: string;
  skills: string[];
  avatar?: string;
  links: { github?: string; x?: string; site?: string; zenn?: string; qiita?: string };
  projects: Project[];
  joinedAt?: string;
};

const DIR = path.join(process.cwd(), "content", "members");
const ID_RE = /^[a-z0-9][a-z0-9-]*$/;

function fail(file: string, msg: string): never {
  throw new Error(`content/members/${file}: ${msg}`);
}

function str(file: string, v: unknown, key: string, required = false): string | undefined {
  if (v === undefined || v === null || v === "") {
    if (required) fail(file, `"${key}" は必須です`);
    return undefined;
  }
  if (typeof v !== "string") fail(file, `"${key}" は文字列にしてください`);
  return v.trim();
}

function url(file: string, v: unknown, key: string): string | undefined {
  const s = str(file, v, key);
  if (!s) return undefined;
  if (!/^https?:\/\//.test(s)) fail(file, `"${key}" は http(s):// で始まるURLにしてください`);
  return s;
}

function strList(file: string, v: unknown, key: string): string[] {
  if (v === undefined) return [];
  if (!Array.isArray(v) || v.some((x) => typeof x !== "string")) fail(file, `"${key}" は文字列の配列にしてください`);
  return [...new Set((v as string[]).map((x) => x.trim()).filter(Boolean))];
}

function parse(file: string, raw: unknown): Member {
  if (typeof raw !== "object" || raw === null || Array.isArray(raw)) fail(file, "JSONオブジェクトにしてください");
  const r = raw as Record<string, unknown>;
  const id = file.replace(/\.json$/, "");
  if (!ID_RE.test(id)) fail(file, "ファイル名は半角英小文字・数字・ハイフンにしてください (例: taro-yamada.json)");

  const links = (r.links ?? {}) as Record<string, unknown>;
  const projects = r.projects ?? [];
  if (!Array.isArray(projects)) fail(file, `"projects" は配列にしてください`);

  return {
    id,
    name: str(file, r.name, "name", true)!,
    nameKana: str(file, r.nameKana, "nameKana"),
    role: str(file, r.role, "role"),
    bio: str(file, r.bio, "bio"),
    skills: strList(file, r.skills, "skills"),
    avatar: str(file, r.avatar, "avatar"),
    links: {
      github: url(file, links.github, "links.github"),
      x: url(file, links.x, "links.x"),
      site: url(file, links.site, "links.site"),
      zenn: url(file, links.zenn, "links.zenn"),
      qiita: url(file, links.qiita, "links.qiita"),
    },
    projects: projects.map((p, i) => {
      const k = `projects[${i}]`;
      const o = (p ?? {}) as Record<string, unknown>;
      if (o.year !== undefined && typeof o.year !== "number") fail(file, `"${k}.year" は数値にしてください`);
      return {
        title: str(file, o.title, `${k}.title`, true)!,
        description: str(file, o.description, `${k}.description`),
        url: url(file, o.url, `${k}.url`),
        repo: url(file, o.repo, `${k}.repo`),
        tech: strList(file, o.tech, `${k}.tech`),
        year: o.year as number | undefined,
      };
    }),
    joinedAt: str(file, r.joinedAt, "joinedAt"),
  };
}

let cache: Member[] | null = null;

/** content/members/*.json を読み込む。先頭が _ のファイル (テンプレート) は無視する */
export function getMembers(): Member[] {
  if (cache) return cache;
  const files = fs.existsSync(DIR)
    ? fs.readdirSync(DIR).filter((f) => f.endsWith(".json") && !f.startsWith("_"))
    : [];
  cache = files
    .map((f) => {
      let raw: unknown;
      try {
        raw = JSON.parse(fs.readFileSync(path.join(DIR, f), "utf8"));
      } catch (e) {
        fail(f, `JSONとして読めません (${(e as Error).message})`);
      }
      return parse(f, raw);
    })
    .sort((a, b) => (a.nameKana ?? a.name).localeCompare(b.nameKana ?? b.name, "ja"));
  return cache;
}

export function getMember(id: string): Member | undefined {
  return getMembers().find((m) => m.id === id);
}

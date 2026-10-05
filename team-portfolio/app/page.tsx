import { MemberDirectory } from "@/components/MemberDirectory";
import { getMembers } from "@/lib/members";
import { site } from "@/lib/site";

export default function Home() {
  const members = getMembers();
  return (
    <main className="stack">
      <header className="page-head">
        <h1>{site.title}</h1>
        <p className="count">{members.length} 名</p>
      </header>
      <MemberDirectory members={members} />
    </main>
  );
}

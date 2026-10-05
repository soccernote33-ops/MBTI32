import type { Member } from "@/lib/members";

function hue(s: string) {
  let h = 0;
  for (const c of s) h = (h * 31 + c.codePointAt(0)!) % 360;
  return h;
}

export function Avatar({ member, size = 48 }: { member: Member; size?: number }) {
  const style = { width: size, height: size, fontSize: size * 0.42 };
  if (member.avatar) {
    // 静的書き出しなので next/image の最適化は使わない
    // eslint-disable-next-line @next/next/no-img-element
    return <img className="avatar" src={member.avatar} alt="" style={style} />;
  }
  return (
    <span className="avatar" aria-hidden="true" style={{ ...style, background: `hsl(${hue(member.id)} 42% 44%)` }}>
      {member.name.trim().charAt(0)}
    </span>
  );
}

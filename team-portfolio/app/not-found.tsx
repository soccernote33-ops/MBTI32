import Link from "next/link";

export default function NotFound() {
  return (
    <main className="empty">
      <h2>ページが見つかりません</h2>
      <p>URLが変わったか、メンバーの登録が削除された可能性があります。</p>
      <Link href="/" className="btn">一覧へ戻る</Link>
    </main>
  );
}

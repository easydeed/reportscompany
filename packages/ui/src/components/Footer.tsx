export default function Footer() {
  return (
    <footer className="border-t bg-white">
      <div className="mx-auto max-w-6xl px-6 py-8 text-sm text-slate-500">
        © {new Date().getFullYear()} Market Reports • <a className="underline" href="/privacy">Privacy</a> • <a className="underline" href="/terms">Terms</a>
      </div>
    </footer>
  );
}








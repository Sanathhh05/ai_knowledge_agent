import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { useEffect, useState } from "react";

export function TopNav() {
  const router = useRouter();
  const pathname = usePathname();
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    // Basic auth check for email display
    const token = localStorage.getItem("token");
    if (token) {
      fetch("http://127.0.0.1:8000/auth/me", {
        headers: { Authorization: `Bearer ${token}` }
      })
        .then(res => res.json())
        .then(data => {
          if (data.email) setEmail(data.email);
        })
        .catch(() => {});
    }
  }, []);

  function handleLogout() {
    localStorage.removeItem("token");
    router.push("/");
  }

  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)] bg-[var(--bg-primary)]">
      {/* Brand */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-[var(--accent-glow)] text-[var(--accent)]">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
          </svg>
        </div>
        <span className="text-lg font-bold tracking-tight text-[var(--text-primary)]">
          RAMBO
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex items-center space-x-8 text-sm font-medium">
        <Link 
          href="/sources" 
          className={`transition-colors ${pathname === "/sources" ? "text-[var(--text-primary)]" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"}`}
        >
          Library
        </Link>
        <Link 
          href="/chat" 
          className={`transition-colors ${pathname === "/chat" ? "text-[var(--text-primary)]" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"}`}
        >
          Chat
        </Link>
      </nav>

      {/* User Actions */}
      <div className="flex items-center space-x-4 text-sm">
        {email && <span className="text-[var(--text-secondary)]">{email}</span>}
        <button 
          onClick={handleLogout}
          className="p-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
          title="Logout"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
            <polyline points="16 17 21 12 16 7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </svg>
        </button>
      </div>
    </header>
  );
}

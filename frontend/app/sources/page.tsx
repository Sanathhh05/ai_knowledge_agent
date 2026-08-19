"use client";

import { useState, useEffect, useCallback, useRef, ChangeEvent } from "react";
import { useRouter } from "next/navigation";
import { TopNav } from "../../components/Layout/TopNav";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

interface Source {
  id: string;
  name: string;
  source_type: string;
  status: string;
  url: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  chunk_count: number;
}

const TYPE_ICONS: Record<string, string> = {
  pdf: "📄",
  docx: "📝",
  txt: "📋",
  youtube: "▶️",
  web: "🌐",
};

export default function SourcesPage() {
  const router = useRouter();
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [ytUrl, setYtUrl] = useState("");
  const [webUrl, setWebUrl] = useState("");
  const [addingYt, setAddingYt] = useState(false);
  const [addingWeb, setAddingWeb] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const getToken = useCallback(() => {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("token");
  }, []);

  const authHeaders = useCallback((): Record<string, string> => {
    const token = getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }, [getToken]);

  const fetchSources = useCallback(async () => {
    const token = getToken();
    if (!token) {
      router.push("/");
      return;
    }
    try {
      const res = await fetch(`${API}/sources`, {
        headers: authHeaders(),
      });
      if (res.status === 401) {
        localStorage.removeItem("token");
        router.push("/");
        return;
      }
      if (!res.ok) throw new Error("Failed to load sources");
      const data: Source[] = await res.json();
      setSources(data);
    } catch {
      setError("Failed to load sources");
    } finally {
      setLoading(false);
    }
  }, [getToken, authHeaders, router]);

  useEffect(() => {
    fetchSources();
  }, [fetchSources]);

  async function handleFileUpload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(`${API}/sources/upload`, {
        method: "POST",
        headers: authHeaders(),
        body: formData,
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Upload failed (${res.status})`);
      }
      await fetchSources();
      setShowAddForm(false);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function handleAddYouTube() {
    if (!ytUrl.trim()) return;
    setAddingYt(true);
    setError("");
    try {
      const res = await fetch(`${API}/sources/youtube`, {
        method: "POST",
        headers: { ...authHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ url: ytUrl }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Failed (${res.status})`);
      }
      setYtUrl("");
      await fetchSources();
      setShowAddForm(false);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to add YouTube");
    } finally {
      setAddingYt(false);
    }
  }

  async function handleAddWebUrl() {
    if (!webUrl.trim()) return;
    setAddingWeb(true);
    setError("");
    try {
      const res = await fetch(`${API}/sources/url`, {
        method: "POST",
        headers: { ...authHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ url: webUrl }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Failed (${res.status})`);
      }
      setWebUrl("");
      await fetchSources();
      setShowAddForm(false);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to add web URL");
    } finally {
      setAddingWeb(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this source from your library?")) return;
    try {
      const res = await fetch(`${API}/sources/${id}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      if (!res.ok) throw new Error("Delete failed");
      await fetchSources();
    } catch {
      setError("Failed to delete source");
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-[var(--text-secondary)]">
        Loading library...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] flex flex-col">
      <TopNav />

      <main className="flex-1 w-full max-w-4xl mx-auto p-6 pt-12">
        {/* Header Section */}
        <div className="mb-10 flex items-end justify-between">
          <div>
            <h1 className="text-4xl font-bold text-[var(--text-primary)] mb-2 tracking-tight font-serif">
              Your knowledge library
            </h1>
            <p className="text-[var(--text-secondary)] text-lg">
              {sources.length === 0
                ? "Add a document, video, or link to begin."
                : `${sources.length} source${sources.length > 1 ? "s" : ""} ready to question.`}
            </p>
          </div>
          {sources.length > 0 && !showAddForm && (
            <button
              onClick={() => setShowAddForm(true)}
              className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-5 py-2.5 rounded-xl font-medium transition-colors shadow-lg"
            >
              + Add source
            </button>
          )}
        </div>

        {error && (
          <div className="bg-red-900/20 border border-[var(--danger)] text-[var(--danger)] p-4 rounded-xl mb-6 flex justify-between items-center">
            <span>{error}</span>
            <button onClick={() => setError("")} className="hover:text-red-400">✕</button>
          </div>
        )}

        {/* Empty State */}
        {sources.length === 0 && !showAddForm && (
          <div className="bg-[var(--bg-card)] border border-[var(--border-primary)] rounded-3xl p-16 text-center shadow-xl">
            <div className="w-16 h-16 bg-[var(--bg-secondary)] border border-[var(--border-primary)] rounded-full flex items-center justify-center mx-auto mb-6">
              <span className="text-[var(--accent)] text-2xl">+</span>
            </div>
            <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-3 font-serif">
              Nothing here yet
            </h2>
            <p className="text-[var(--text-secondary)] max-w-md mx-auto mb-10 leading-relaxed">
              Upload a PDF or DOCX, paste a YouTube link, or drop in any article URL — then ask it anything by typing or speaking.
            </p>
            <button
              onClick={() => setShowAddForm(true)}
              className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-8 py-3.5 rounded-xl font-semibold text-lg transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              + Add your first source
            </button>
          </div>
        )}

        {/* Add Source Form */}
        {showAddForm && (
          <div className="bg-[var(--bg-card)] border border-[var(--border-primary)] rounded-3xl p-8 mb-8 shadow-xl relative overflow-hidden">
            <button 
              onClick={() => setShowAddForm(false)}
              className="absolute top-6 right-6 text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            >
              ✕
            </button>
            <h2 className="text-xl font-bold text-[var(--text-primary)] mb-8 font-serif">
              Add to your knowledge
            </h2>

            <div className="grid md:grid-cols-2 gap-8">
              {/* File Upload Block */}
              <div className="bg-[var(--bg-secondary)] border border-dashed border-[var(--border-primary)] rounded-2xl p-6 text-center hover:border-[var(--accent)] transition-colors relative">
                <input
                  ref={fileRef}
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={handleFileUpload}
                  disabled={uploading}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
                />
                <div className="text-3xl mb-3">📄</div>
                <div className="font-medium text-[var(--text-primary)] mb-1">
                  Upload document
                </div>
                <div className="text-sm text-[var(--text-secondary)] mb-4">
                  PDF · DOCX · TXT
                </div>
                <div className="text-sm text-[var(--accent)] font-medium">
                  {uploading ? "Preparing your source..." : "Click to choose a file"}
                </div>
              </div>

              {/* URLs Block */}
              <div className="flex flex-col justify-center space-y-6">
                <div>
                  <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                    YouTube Video
                  </label>
                  <div className="flex gap-3">
                    <input
                      type="url"
                      value={ytUrl}
                      onChange={(e) => setYtUrl(e.target.value)}
                      placeholder="Paste YouTube URL..."
                      disabled={addingYt}
                      className="flex-1 bg-[var(--bg-input)] border border-[var(--border-primary)] rounded-xl px-4 py-2.5 text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)] transition-colors"
                    />
                    <button
                      onClick={handleAddYouTube}
                      disabled={addingYt || !ytUrl.trim()}
                      className="bg-[var(--bg-secondary)] hover:bg-[var(--accent)] hover:text-white border border-[var(--border-primary)] hover:border-[var(--accent)] text-[var(--text-primary)] px-5 rounded-xl font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {addingYt ? "..." : "Add"}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                    Web Article
                  </label>
                  <div className="flex gap-3">
                    <input
                      type="url"
                      value={webUrl}
                      onChange={(e) => setWebUrl(e.target.value)}
                      placeholder="Paste article URL..."
                      disabled={addingWeb}
                      className="flex-1 bg-[var(--bg-input)] border border-[var(--border-primary)] rounded-xl px-4 py-2.5 text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)] transition-colors"
                    />
                    <button
                      onClick={handleAddWebUrl}
                      disabled={addingWeb || !webUrl.trim()}
                      className="bg-[var(--bg-secondary)] hover:bg-[var(--accent)] hover:text-white border border-[var(--border-primary)] hover:border-[var(--accent)] text-[var(--text-primary)] px-5 rounded-xl font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {addingWeb ? "..." : "Add"}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Source List */}
        {sources.length > 0 && (
          <div className="space-y-4">
            {sources.map((s) => (
              <div
                key={s.id}
                className="bg-[var(--bg-card)] border border-[var(--border-primary)] hover:border-[var(--border-focus)] transition-colors rounded-2xl p-5 flex items-center justify-between group"
              >
                <div className="flex items-center gap-4 overflow-hidden">
                  <div className="w-12 h-12 rounded-xl bg-[var(--bg-secondary)] flex items-center justify-center text-xl shrink-0">
                    {TYPE_ICONS[s.source_type] || "📁"}
                  </div>
                  <div className="min-w-0">
                    <div className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1">
                      {s.source_type}
                    </div>
                    <div className="font-medium text-[var(--text-primary)] truncate text-lg">
                      {s.name}
                    </div>
                    <div className="text-sm mt-1 flex items-center gap-3">
                      {s.status === "completed" ? (
                        <span className="text-[var(--text-secondary)]">Ready</span>
                      ) : s.status === "processing" ? (
                        <span className="text-[var(--warning)] animate-pulse">Preparing...</span>
                      ) : (
                        <span className="text-[var(--danger)]" title={s.error_message || ""}>Failed</span>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => router.push("/chat")}
                    className="px-4 py-2 bg-[var(--bg-secondary)] hover:bg-[var(--accent)] hover:text-white text-[var(--text-primary)] border border-[var(--border-primary)] hover:border-[var(--accent)] rounded-lg text-sm font-medium transition-colors"
                  >
                    Chat
                  </button>
                  <button
                    onClick={() => handleDelete(s.id)}
                    className="p-2 text-[var(--text-secondary)] hover:bg-red-900/30 hover:text-[var(--danger)] rounded-lg transition-colors"
                    title="Delete source"
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="3 6 5 6 21 6"></polyline>
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

import React from "react";
import { Conversation } from "../../lib/api/chat";

interface ChatSidebarProps {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onDelete: (id: string) => void;
}

export function ChatSidebar({ conversations, activeId, onSelect, onNewChat, onDelete }: ChatSidebarProps) {
  return (
    <div className="w-[280px] border-r border-[var(--border-primary)] bg-[var(--bg-secondary)] flex flex-col shrink-0">
      <div className="p-4 border-b border-[var(--border-primary)]">
        <button
          onClick={onNewChat}
          className="w-full py-3 bg-[var(--bg-card)] hover:bg-[var(--accent)] text-[var(--text-primary)] hover:text-white border border-[var(--border-primary)] hover:border-[var(--accent)] rounded-xl font-medium flex items-center justify-center gap-2 transition-all shadow-sm"
        >
          <span className="text-lg leading-none">+</span> New Chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-1 scrollbar-hide">
        <div className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-3 px-2">
          Recent
        </div>
        {conversations.length === 0 ? (
          <div className="text-[var(--text-secondary)] text-sm text-center mt-8">
            No conversations yet.
          </div>
        ) : (
          conversations.map(conv => (
            <div
              key={conv.id}
              className={`group flex items-center justify-between px-3 py-2.5 rounded-xl cursor-pointer transition-colors ${
                activeId === conv.id 
                  ? "bg-[var(--accent-glow)] text-[var(--accent)]" 
                  : "hover:bg-[var(--bg-card)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              }`}
              onClick={() => onSelect(conv.id)}
            >
              <div className={`truncate text-sm ${activeId === conv.id ? "font-semibold" : "font-medium"}`}>
                {conv.title || "New Chat"}
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(conv.id);
                }}
                className="opacity-0 group-hover:opacity-100 p-1.5 text-[var(--text-muted)] hover:text-[var(--danger)] hover:bg-red-900/20 rounded-md transition-all"
                title="Delete"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

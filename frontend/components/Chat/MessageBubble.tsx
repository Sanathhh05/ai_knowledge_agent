import React from "react";
import { ChatMessage, Citation } from "../../lib/api/chat";
import ReactMarkdown from "react-markdown";

interface MessageBubbleProps {
  message: ChatMessage;
}

const TYPE_ICONS: Record<string, string> = {
  pdf: "📄",
  docx: "📝",
  txt: "📋",
  youtube: "▶️",
  web: "🌐",
};

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  // Determine the primary source to display
  let primarySource: Citation | null = null;
  if (!isUser && message.sources && message.sources.length > 0) {
    // Group by source_id to avoid showing multiple chunks from same source
    const groupedSources = new Map<string, Citation>();
    for (const src of message.sources) {
      if (!groupedSources.has(src.source_id)) {
        groupedSources.set(src.source_id, src);
      } else {
        // Keep the one with the higher score
        const existing = groupedSources.get(src.source_id)!;
        if (src.score > existing.score) {
          groupedSources.set(src.source_id, src);
        }
      }
    }
    
    // Convert to array and sort by score descending
    const uniqueSources = Array.from(groupedSources.values()).sort((a, b) => b.score - a.score);
    
    // Pick the top one as the primary source
    if (uniqueSources.length > 0) {
      primarySource = uniqueSources[0];
    }
  }

  let metaInfo = "";
  if (primarySource?.metadata) {
    if (primarySource.metadata.page) metaInfo = `Page ${primarySource.metadata.page}`;
    else if (primarySource.metadata.source_type === "youtube") metaInfo = "YouTube Video";
    else if (primarySource.metadata.source_type === "web") metaInfo = "Web Page";
    else metaInfo = "Document";
  }

  return (
    <div className={`flex flex-col w-full mb-8 ${isUser ? "items-end" : "items-start"}`}>
      <div 
        className={`max-w-[85%] rounded-2xl p-6 ${
          isUser 
            ? "bg-[var(--accent)] text-white" 
            : "bg-[var(--bg-card)] text-[var(--text-primary)] border border-[var(--border-primary)] shadow-sm"
        }`}
      >
        <div className="prose prose-invert max-w-none text-[15px] leading-relaxed">
          {isUser ? (
            <div className="whitespace-pre-wrap">{message.content}</div>
          ) : (
            <ReactMarkdown>{message.content}</ReactMarkdown>
          )}
        </div>
        
        {primarySource && (
          <div className="mt-6 pt-5 border-t border-[var(--border-primary)]">
            <div className="text-[11px] font-bold text-[var(--text-muted)] uppercase tracking-widest mb-3">
              Source
            </div>
            <div className="inline-flex items-center gap-3 bg-[var(--bg-secondary)] border border-[var(--border-primary)] rounded-xl px-4 py-3 max-w-full">
              <div className="text-xl shrink-0 opacity-80">
                {TYPE_ICONS[primarySource.metadata?.source_type || ""] || "📄"}
              </div>
              <div className="min-w-0 overflow-hidden">
                <div className="font-semibold text-[var(--text-primary)] truncate text-sm">
                  {primarySource.source_name}
                </div>
                <div className="text-xs text-[var(--text-secondary)] mt-0.5">
                  Primary source · {metaInfo}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

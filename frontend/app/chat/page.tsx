"use client";

import React, { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { ChatSidebar } from "../../components/Chat/ChatSidebar";
import { MessageBubble } from "../../components/Chat/MessageBubble";
import { TopNav } from "../../components/Layout/TopNav";
import {
  Conversation,
  ChatMessage,
  fetchConversations,
  createConversation,
  getConversation,
  deleteConversation,
  sendMessage,
  sendVoiceMessage
} from "../../lib/api/chat";

export default function ChatPage() {
  const router = useRouter();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Voice state
  const [recording, setRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/");
      return;
    }
    loadConversations();
  }, [router]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function loadConversations() {
    try {
      const data = await fetchConversations();
      setConversations(data);
    } catch (e) {
      console.error(e);
      if (e instanceof Error && e.message.includes("401")) {
        router.push("/");
      }
    }
  }

  async function handleSelect(id: string) {
    setActiveConvId(id);
    stopTTS();
    try {
      const detail = await getConversation(id);
      setMessages(detail.messages);
    } catch (e) {
      console.error(e);
    }
  }

  async function handleNewChat() {
    stopTTS();
    try {
      const conv = await createConversation();
      setConversations([conv, ...conversations]);
      setActiveConvId(conv.id);
      setMessages([]);
    } catch (e) {
      console.error(e);
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteConversation(id);
      setConversations(conversations.filter(c => c.id !== id));
      if (activeConvId === id) {
        setActiveConvId(null);
        setMessages([]);
      }
    } catch (e) {
      console.error(e);
    }
  }

  // --- Voice / TTS Logic ---
  function stopTTS() {
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
  }

  function playAudioResponse(text: string) {
    if (typeof window === 'undefined' || !window.speechSynthesis) return;
    stopTTS();
    // Strip citation brackets like [Source Name]
    const cleanText = text.replace(/\[.*?\]/g, '');
    const utterance = new SpeechSynthesisUtterance(cleanText);
    window.speechSynthesis.speak(utterance);
  }

  async function handleStartRecording() {
    stopTTS();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : '';
      const mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType || 'audio/wav' });
        stream.getTracks().forEach(track => track.stop());
        await processVoiceAudio(audioBlob);
      };

      mediaRecorder.start();
      setRecording(true);
      setRecordingTime(0);
      
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => {
          if (prev >= 59) {
            handleStopRecording();
            return 60;
          }
          return prev + 1;
        });
      }, 1000);

    } catch (e) {
      alert("Microphone access is required for voice questions.");
    }
  }

  function handleStopRecording() {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop();
    }
    setRecording(false);
    if (timerRef.current) clearInterval(timerRef.current);
  }

  async function processVoiceAudio(audioBlob: Blob) {
    if (loading) return;
    
    let convId = activeConvId;
    if (!convId) {
      try {
        const conv = await createConversation();
        setConversations([conv, ...conversations]);
        convId = conv.id;
        setActiveConvId(conv.id);
      } catch (e) {
        console.error("Failed to create conversation");
        return;
      }
    }

    setLoading(true);

    try {
      const res = await sendVoiceMessage(convId, audioBlob);
      setMessages(prev => {
        const userMsg = res.user_message || {
          id: "voice-" + Date.now(),
          role: "user" as const,
          content: "🎤 (Voice Message)",
          created_at: new Date().toISOString()
        };
        const aiMsg = { ...res.message, sources: res.sources };
        return [...prev, userMsg, aiMsg];
      });
      playAudioResponse(res.message.content);
      loadConversations();
    } catch (err: any) {
      alert(err.message || "Failed to process voice message");
    } finally {
      setLoading(false);
    }
  }

  async function handleSend(e?: React.FormEvent) {
    e?.preventDefault();
    if (!inputText.trim() || loading || recording) return;

    let convId = activeConvId;
    if (!convId) {
      try {
        const conv = await createConversation();
        setConversations([conv, ...conversations]);
        convId = conv.id;
        setActiveConvId(conv.id);
      } catch (e) {
        console.error("Failed to create conversation");
        return;
      }
    }

    const textToSend = inputText;
    setInputText("");
    setLoading(true);

    const tempUserMsg: ChatMessage = {
      id: "temp-" + Date.now(),
      role: "user",
      content: textToSend,
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, tempUserMsg]);

    try {
      const res = await sendMessage(convId, textToSend);
      setMessages(prev => {
        const newMsg = { ...res.message, sources: res.sources };
        const filtered = prev.filter(m => m.id !== tempUserMsg.id);
        const finalUserMsg = res.user_message || tempUserMsg;
        return [...filtered, finalUserMsg, newMsg];
      });
      loadConversations();
    } catch (err: any) {
      alert(err.message || "Failed to send message");
      setMessages(prev => prev.filter(m => m.id !== tempUserMsg.id));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-screen bg-[var(--bg-primary)]">
      <TopNav />
      <div className="flex flex-1 overflow-hidden">
        <ChatSidebar
          conversations={conversations}
          activeId={activeConvId}
          onSelect={handleSelect}
          onNewChat={handleNewChat}
          onDelete={handleDelete}
        />
        <div className="flex-1 flex flex-col overflow-hidden">
          
          {/* Header */}
          <div className="px-8 py-4 border-b border-[var(--border-primary)] bg-[var(--bg-primary)] flex justify-between items-center shrink-0">
            <h2 className="text-xl font-serif font-bold text-[var(--text-primary)] tracking-tight">RAMBO Chat</h2>
            <div className="flex items-center gap-4">
              <span className="text-sm font-medium text-[var(--text-secondary)]">
                {typeof window !== 'undefined' && 'speechSynthesis' in window ? "🔊 TTS Active" : "🔇 TTS Unavailable"}
              </span>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-8 scrollbar-hide">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-[var(--text-secondary)]">
                <div className="w-16 h-16 rounded-full bg-[var(--bg-secondary)] flex items-center justify-center mb-6 border border-[var(--border-primary)] shadow-sm">
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                  </svg>
                </div>
                <h3 className="text-2xl font-bold text-[var(--text-primary)] mb-2 font-serif">How can I help you today?</h3>
                <p className="text-lg">Ask anything about your knowledge library.</p>
                <div className="mt-8 px-6 py-3 rounded-full bg-[var(--bg-secondary)] border border-[var(--border-primary)] text-sm shadow-sm">
                  Try typing or use the microphone 🎤
                </div>
              </div>
            ) : (
              <div className="max-w-3xl mx-auto w-full">
                {messages.map(msg => (
                  <MessageBubble key={msg.id} message={msg} />
                ))}
                {loading && (
                  <div className="flex items-center gap-3 text-[var(--text-secondary)] mb-8 animate-pulse ml-2">
                    <div className="w-2 h-2 rounded-full bg-[var(--accent)]"></div>
                    <div className="text-sm font-medium">RAMBO is thinking...</div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Input Composer */}
          <div className="p-6 bg-[var(--bg-primary)]">
            <div className="max-w-3xl mx-auto">
              <form 
                onSubmit={handleSend} 
                className={`flex items-center gap-2 p-2 bg-[var(--bg-card)] border rounded-2xl transition-colors shadow-lg ${
                  recording ? "border-[var(--danger)]" : "border-[var(--border-primary)] focus-within:border-[var(--accent)]"
                }`}
              >
                {recording ? (
                  <button
                    type="button"
                    onClick={handleStopRecording}
                    className="h-12 px-6 rounded-xl bg-[var(--danger)] text-white font-bold flex items-center gap-3 hover:bg-red-600 transition-colors shrink-0 shadow-md"
                  >
                    <div className="w-3 h-3 bg-white rounded-sm animate-pulse"></div>
                    <span>{recordingTime}s</span>
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={handleStartRecording}
                    disabled={loading}
                    title="Start voice recording"
                    className="h-12 w-12 rounded-xl text-[var(--text-secondary)] hover:text-[var(--accent)] hover:bg-[var(--accent-glow)] flex items-center justify-center transition-all shrink-0 disabled:opacity-50"
                  >
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
                      <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                      <line x1="12" y1="19" x2="12" y2="22"></line>
                    </svg>
                  </button>
                )}
                
                <input
                  type="text"
                  value={inputText}
                  onChange={e => setInputText(e.target.value)}
                  placeholder={recording ? "Recording..." : "Ask your sources..."}
                  disabled={loading || recording}
                  className="flex-1 bg-transparent border-none text-[var(--text-primary)] placeholder-[var(--text-muted)] px-3 py-2 outline-none text-[15px] disabled:opacity-50"
                />
                
                <button
                  type="submit"
                  disabled={loading || recording || !inputText.trim()}
                  className="h-12 w-12 rounded-xl bg-[var(--accent)] text-white flex items-center justify-center transition-all shrink-0 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[var(--accent-hover)] shadow-md"
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="22" y1="2" x2="11" y2="13"></line>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                  </svg>
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

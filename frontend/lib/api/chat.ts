const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

function getAuthHeaders() {
  const token = localStorage.getItem("token");
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

export interface Conversation {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  source_id: string;
  source_name: string;
  chunk_id: string;
  score: number;
  metadata: any;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
  sources?: Citation[]; // Only attached by frontend contextually or merged
}

export interface ConversationDetail extends Conversation {
  messages: ChatMessage[];
}

export interface ChatTurnResponse {
  message: ChatMessage;
  user_message?: ChatMessage;
  sources: Citation[];
}

export async function fetchConversations(): Promise<Conversation[]> {
  const res = await fetch(`${API}/conversations/`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to fetch conversations");
  return res.json();
}

export async function createConversation(): Promise<Conversation> {
  const res = await fetch(`${API}/conversations/`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({}),
  });
  if (!res.ok) throw new Error("Failed to create conversation");
  return res.json();
}

export async function getConversation(id: string): Promise<ConversationDetail> {
  const res = await fetch(`${API}/conversations/${id}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to fetch conversation details");
  return res.json();
}

export async function deleteConversation(id: string): Promise<void> {
  const res = await fetch(`${API}/conversations/${id}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to delete conversation");
}

export async function sendMessage(conversationId: string, content: string): Promise<ChatTurnResponse> {
  const res = await fetch(`${API}/conversations/${conversationId}/messages`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ content }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to send message");
  }
  return res.json();
}

export async function sendVoiceMessage(conversationId: string, audioBlob: Blob): Promise<ChatTurnResponse> {
  const token = localStorage.getItem("token");
  const formData = new FormData();
  formData.append("audio", audioBlob, "audio.webm");

  const res = await fetch(`${API}/conversations/${conversationId}/voice`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}` // Note: NO Content-Type, let browser set boundary
    },
    body: formData,
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to send voice message");
  }
  return res.json();
}

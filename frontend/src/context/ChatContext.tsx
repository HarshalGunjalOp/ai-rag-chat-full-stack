// src/context/ChatContext.tsx
import React, { createContext, useContext, useEffect, useState } from 'react';
import { v4 as uuid } from 'uuid';
import * as api from '../api/chatApi';
import { useKeyboardShortcut } from '../hooks/useKeyboardShortcut.ts';
import { getConversationMessages } from '../api/chatApi.ts';

type Conversation = { id: string; title: string; timestamp: string };
type Message = {
  id: string;
  type: 'user' | 'assistant';
  text: string;
  createdAt: string;
  sources?: string[];
};

interface ChatState {
  user_id: string;
  conversations: Conversation[];
  currentConv: Conversation | null;
  messages: Message[];
  isLoading: boolean;
  docStatus: { count: number; chunks: number } | null;
  connectionOk: boolean;
  sidebarCollapsed: boolean;
}

const ChatCtx = createContext<ReturnType<typeof useChatController> | null>(null);

export const ChatProvider: React.FC<React.PropsWithChildren> = ({ children }) => {
  const controller = useChatController();
  return <ChatCtx.Provider value={controller}>{children}</ChatCtx.Provider>;
};

export const useChat = () => {
  const ctx = useContext(ChatCtx);
  if (!ctx) throw new Error('useChat must be inside provider');
  return ctx;
};

/* ---------------- private ---------------- */

function useChatController() {
  type Notification = { id: string; text: string; kind: 'success' | 'error' };
  const [user_id] = useState(
    () =>
      localStorage.getItem('chat_user_id') ??
      (() => {
        const id = `user-${uuid()}`;
        localStorage.setItem('chat_user_id', id);
        return id;
      })()
  );
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConv, setCurrentConv] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setLoading] = useState(false);
  const [docStatus, setDocStatus] = useState<{ count: number; chunks: number } | null>(null);
  const [connectionOk, setConnectionOk] = useState(true);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const addNotification = (text: string, kind: 'success' | 'error') => {
    const id = uuid();
    setNotifications(n => [...n, { id, text, kind }]);
  };

  const removeNotification = (id: string) => {
    setNotifications(n => n.filter(notif => notif.id !== id));
  };

  /* initial load */
  useEffect(() => {
    refreshDocStatus();
    api.listConversations(user_id).then(setConversations);
    // eslint-disable-next-line
  }, []);

  useKeyboardShortcut('ctrl+b', () => setSidebarCollapsed(prev => !prev));
  useKeyboardShortcut('ctrl+i', () => clearChat());

  const toggleSidebar = () => {
    setSidebarCollapsed(prev => !prev);
  };

  async function refreshDocStatus() {
    try {
      const d = await api.documentsStatus(user_id);
      setDocStatus({ count: d.documentCount, chunks: d.totalChunks });
      setConnectionOk(true);
    } catch {
      setConnectionOk(false);
    }
  }

  /* messages */
  const addUserMessage = (text: string) =>
    setMessages(m => [
      ...m,
      { id: uuid(), type: 'user', text, createdAt: new Date().toISOString() },
    ]);

  /* called for every token */
  const appendStreamChunk = (delta: string) =>
    setMessages(m => {
      const idx = m.length - 1;
      if (idx >= 0 && m[idx].type === 'assistant' && !m[idx].sources) {
        /* build a fresh object – never touch the one in state */
        const updated = { ...m[idx], text: m[idx].text + delta };
        return [...m.slice(0, idx), updated];
      }
      return m;
    });
  /* called once, when the backend sends `type:"complete"` */
  const finaliseAssistant = (fullText: string | undefined, sources?: string[]) =>
    setMessages(m => {
      const last = m[m.length - 1];
      if (last && last.type === 'assistant') {
        if (fullText !== undefined) {
          // only overwrite if we were given one
          last.text = fullText;
        }
        last.sources = sources;
        return [...m.slice(0, -1), { ...last }];
      }
      return m;
    });
  const pushAssistantPlaceholder = () =>
    setMessages(m => [
      ...m,
      { id: uuid(), type: 'assistant', text: '', createdAt: new Date().toISOString() },
    ]);

  const clearChat = () => {
    setMessages([]);
    setCurrentConv(null);
  };

  async function loadConversationMessages(conversation_id: string | number) {
  // Convert to string first
  const convId = String(conversation_id)
  
  // Don't try to load messages for temporary conversations
  if (convId.startsWith("temp-")) {
    setMessages([]) // Clear messages for temp conversations
    return
  }
  
  try {
    setLoading(true)
    setMessages([]) // Clear current messages
    const messages = await api.getConversationMessages(convId)
    
    const transformedMessages = messages.map((msg: any) => ({
      id: msg.id.toString(),
      type: msg.messagetype,
      text: typeof msg.content === "string" ? msg.content : msg.content.text,
      createdAt: msg.createdat,
      sources: msg.content.sources || undefined,
    }))
    
    setMessages(transformedMessages)
  } catch (error) {
    console.error("Error loading conversation messages:", error)
    addNotification("Failed to load conversation messages", "error")
    setMessages([]) // Clear messages on error
  } finally {
    setLoading(false)
  }
}


  return {
    /* state */
    user_id,
    conversations,
    currentConv,
    messages,
    isLoading,
    docStatus,
    connectionOk,
    /* actions */
    setLoading,
    addUserMessage,
    pushAssistantPlaceholder,
    setCurrentConv,
    setConversations,
    refreshDocStatus,
    clearChat,
    loadConversationMessages,
    sidebarCollapsed,
    toggleSidebar,
    /* Notification */
    notifications,
    addNotification,
    removeNotification,
    appendStreamChunk,
    finaliseAssistant,
  } as const;
}

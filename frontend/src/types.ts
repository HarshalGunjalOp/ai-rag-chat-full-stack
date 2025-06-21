export type Conversation = {
  id: string;
  title: string;
  timestamp: string;
};

export type Message = {
  id: string;
  type: 'user' | 'assistant';
  text: string;
  createdAt: string;
  sources?: string[];
};

export type Notification = { id: string; text: string; kind: 'success' | 'error' };

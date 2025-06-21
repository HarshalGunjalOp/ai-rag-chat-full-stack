// src/api/chatApi.ts
const base = import.meta.env.VITE_API_BASE_URL + '/api/v1/chat';

export function listConversations(user: string) {
  return fetch(`${base}/conversations?user_id=${user}`).then(r => r.json());
}

export function documentsStatus(user: string) {
  return fetch(`${base}/documents/status?user_id=${user}`).then(r => {
    if (!r.ok) throw new Error();
    return r.json();
  });
}

export async function uploadFiles(user: string, files: File[]) {
  const fd = new FormData();
  files.forEach(f => fd.append('files', f));
  fd.append('user_id', user);
  return fetch(`${base}/upload/multiple`, { method: 'POST', body: fd }).then(r => r.json());
}

export function streamMessage(
  user: string,
  prompt: string,
  conversationId?: string,
  signal?: AbortSignal
) {
  return fetch(`${base}/messages/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content: prompt, conversationId, user_id: user }),
    signal,
  });
}

export function clearDocuments(user: string) {
  return fetch(`${base}/documents/clear?user_id=${user}`, { method: 'DELETE' });
}

export function getConversationMessages(conversationId: string) {
  return fetch(`${base}/conversations/${conversationId}/messages`).then(r => {
    if (!r.ok) {
      throw new Error(`Failed to fetch messages: ${r.status}`);
    }
    return r.json();
  });
}

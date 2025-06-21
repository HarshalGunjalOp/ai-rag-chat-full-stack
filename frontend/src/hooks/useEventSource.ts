// src/hooks/useEventSource.ts
import { useRef } from 'react';
export function useEventSource() {
  const controllerRef = useRef<AbortController | null>(null);

  function abort() {
    controllerRef.current?.abort();
  }

  async function consume(
    response: Response,
    onChunk: (text: string) => void,
    onComplete: (meta: any) => void
  ) {
    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buf = '';
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const lines = buf.split('\n');
      buf = lines.pop() || '';
      for (const l of lines) {
        if (!l.startsWith('data:')) continue;
        const obj = JSON.parse(l.slice(6));
        if (obj.type === 'chunk') onChunk(obj.content ?? '');
        else if (obj.type === 'complete') {
          onComplete(obj);
        }
      }
    }
  }

  return { abort, consume, controllerRef };
}

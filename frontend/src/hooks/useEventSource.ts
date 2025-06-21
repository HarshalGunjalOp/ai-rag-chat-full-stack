
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
    let buf = "";

    try {
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;

        buf += decoder.decode(value, { stream: true });
        const lines = buf.split("\n");
        buf = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          
          const dataStr = line.slice(6);
          if (dataStr === "[DONE]") return;
          
          try {
            // Handle both JSON and plain text responses
            if (dataStr.startsWith("{")) {
              const obj = JSON.parse(dataStr);
              
              if (obj.type === "chunk") {
                onChunk(obj.content ?? "");
              } else if (obj.type === "complete") {
                onComplete(obj);
              } else if (obj.type === "error") {
                console.error("Server error:", obj.message);
                return;
              }
            } else {
              // Handle plain text streaming (your backend might be sending this)
              onChunk(dataStr);
            }
          } catch (e) {
            // If it's not JSON, treat as plain text
            onChunk(dataStr);
          }
        }
      }
    } catch (error) {
      console.error("Stream consumption error:", error);
      throw error;
    }
  }

  return { abort, consume, controllerRef };
}


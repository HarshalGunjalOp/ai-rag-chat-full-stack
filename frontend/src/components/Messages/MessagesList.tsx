import { useEffect, useRef } from 'react';
import { useChat } from '../../context/ChatContext';
import MessageBubble from './MessageBubble';
import { RocketLaunchIcon } from '@heroicons/react/24/solid';

export default function MessagesList() {
  const { messages } = useChat();
  const containerRef = useRef<HTMLDivElement>(null);

  /* auto-scroll */
  useEffect(() => {
    const el = containerRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  return (
    <section ref={containerRef} className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-4">
      {messages.length === 0 ? (
        <div className="text-center py-64 max-w-md mx-auto">
          <RocketLaunchIcon className="w-12 h-12 mx-auto text-accent-purple mb-4" />
          <h3 className="text-xl font-semibold mb-2">Welcome to AI Chat</h3>
          <p className="text-gray-400">
            Upload documents and start asking questions. I’ll help you find answers using advanced
            AI.
          </p>
        </div>
      ) : (
        messages.map(m => <MessageBubble key={m.id} msg={m} />)
      )}
    </section>
  );
}

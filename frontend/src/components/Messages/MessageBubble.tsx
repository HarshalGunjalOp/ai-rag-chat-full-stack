// src/components/Messages/MessageBubble.tsx
import {ChatBubbleLeftEllipsisIcon} from '@heroicons/react/24/solid';
import {clsx} from 'clsx';

export default function MessageBubble({msg}: {msg: {
  id: string;
  type: 'user' | 'assistant';
  text: string;
  createdAt: string;
  sources?: string[];
}}) {
  const isUser = msg.type === 'user';
  return (
    <div className={clsx('mb-4 flex', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={clsx(
          'rounded-lg px-4 py-2 max-w-xs lg:max-w-md xl:max-w-lg whitespace-pre-wrap text-sm',
          isUser
            ? 'bg-accent-purple text-white'
            : 'bg-dark-secondary text-white',
        )}>
        <p>{msg.text || <ChatBubbleLeftEllipsisIcon className="w-5 h-5 animate-pulse" />}</p>

        {msg.sources?.length>0 && (
          <div className="mt-2 pt-2 border-t border-gray-600">
            <p className="text-xs text-gray-400 mb-1">Sources:</p>
            <div className="flex flex-wrap gap-1">
              {msg.sources.map(s => (
                <span
                  key={s}
                  className="text-xs bg-dark-tertiary px-2 py-1 rounded">
                  {s}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

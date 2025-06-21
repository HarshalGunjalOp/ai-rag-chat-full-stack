
import { ChatBubbleLeftEllipsisIcon } from '@heroicons/react/24/solid'
import clsx from 'clsx'

export default function MessageBubble({ msg }: { msg: { id: string; type: 'user' | 'assistant'; text: string; createdAt: string; sources?: string[] } }) {
  const isUser = msg.type === 'user'

  return (
    <div className={clsx("mb-6 flex items-start gap-3", isUser ? "justify-end" : "justify-start")}>
      {/* Assistant Avatar/Icon */}
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center">
          <ChatBubbleLeftEllipsisIcon className="w-4 h-4 text-white" />
        </div>
      )}

      {/* Message Bubble */}
      <div className={clsx(
        "relative max-w-xs sm:max-w-md lg:max-w-lg xl:max-w-xl",
        "px-4 py-3 rounded-2xl shadow-sm",
        "whitespace-pre-wrap text-sm leading-relaxed",
        isUser
          ? "bg-purple-600 text-white rounded-br-md" // User bubble (right side)
          : "bg-gray-700 text-white rounded-bl-md"    // Assistant bubble (left side)
      )}>
        {/* Message bubble tail */}
        <div className={clsx(
          "absolute top-0 w-0 h-0",
          isUser
            ? "right-0 border-l-8 border-l-purple-600 border-t-8 border-t-transparent border-b-8 border-b-transparent transform translate-x-2"
            : "left-0 border-r-8 border-r-gray-700 border-t-8 border-t-transparent border-b-8 border-b-transparent transform -translate-x-2"
        )} />

        <p className="mb-0">{msg.text}</p>

        {/* Loading indicator for assistant messages */}
        {!isUser && msg.text === '' && (
          <div className="flex items-center gap-1">
            <ChatBubbleLeftEllipsisIcon className="w-4 h-4 animate-pulse opacity-60" />
            <span className="text-xs opacity-60">Thinking...</span>
          </div>
        )}

        {/* Sources section */}
        {msg.sources && msg.sources.length > 0 && (
          <div className="mt-3 pt-2 border-t border-gray-600/50">
            <p className="text-xs opacity-70 mb-2">Sources:</p>
            <div className="flex flex-wrap gap-1">
              {msg.sources.map((s) => (
                <span key={s} className="text-xs bg-black/20 px-2 py-1 rounded">
                  {s}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Timestamp */}
        <div className={clsx(
          "text-xs opacity-60 mt-2",
          isUser ? "text-right" : "text-left"
        )}>
          {new Date(msg.createdAt).toLocaleTimeString()}
        </div>
      </div>

      {/* User Avatar/Icon */}
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
          <span className="text-white text-sm font-medium">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
            </svg>

          </span>
        </div>
      )}
    </div>
  )
}


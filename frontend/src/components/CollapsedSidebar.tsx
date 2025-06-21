import { PlusIcon, ChevronRightIcon } from '@heroicons/react/24/solid';
import { useChat } from '../context/ChatContext';

export default function CollapsedSidebar() {
  const { toggleSidebar, clearChat } = useChat();

  return (
    <aside className="w-16 bg-dark-secondary border-r border-dark-tertiary flex flex-col items-center">
      {/* New Chat Button */}
      <div className="p-3 mt-2 border-b h-18 border-dark-tertiary w-full">
        <button
          onClick={clearChat}
          className="w-10 h-10 bg-purple-800 hover:bg-purple-600 text-white rounded-lg flex items-center justify-center"
          title="New Chat (Ctrl+I)"
        >
          <PlusIcon className="w-5 h-5" />
        </button>
      </div>

      {/* Spacer */}
      <div className="flex-1"></div>

      {/* Expand Button - Bottom */}
      <div className="p-3 border-dark-tertiary w-full">
        <button
          onClick={toggleSidebar}
          className="w-10 h-10 text-gray-100 hover:text-white bg-purple-800 hover:bg-purple-600 rounded-lg flex items-center justify-center"
          title="Expand sidebar (Ctrl+B)"
        >
          <ChevronRightIcon className="w-5 h-5" />
        </button>
      </div>
    </aside>
  );
}

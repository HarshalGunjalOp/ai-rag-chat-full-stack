

import { PlusIcon, ChevronLeftIcon } from '@heroicons/react/24/solid';
import { useChat } from '../context/ChatContext.tsx';
import ConversationItem from './ConversationItem';

export default function Sidebar() {
  const { 
    conversations, 
    currentConv, 
    setCurrentConv, 
    clearChat, 
    docStatus, 
    loadConversationMessages,
    toggleSidebar 
  } = useChat();

  const handleConversationClick = async (conv: any) => {
    setCurrentConv(conv);
    await loadConversationMessages(conv.id);
  };

  return (
    <aside className="w-80 bg-dark-secondary border-r border-dark-tertiary flex flex-col">
      {/* Header */}
      <header className="px-4 py-3 border-b border-dark-tertiary h-20">
        <div className="flex items-center justify-between my-3">
          <h1 className="text-xl font-bold text-white">AI Chat</h1>
          <button
            onClick={clearChat}
            className="bg-purple-800 hover:bg-purple-600 text-white px-4 py-2 rounded-lg text-sm font-medium"
          >
            <PlusIcon className="w-4 h-4 mr-1 inline" />
            New Chat
          </button>
        </div>
        
      </header>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-2">
        {conversations.map(c => (
          <ConversationItem
            key={c.id}
            conv={c}
            active={currentConv?.id === c.id}
            onClick={() => handleConversationClick(c)}
          />
        ))}
      </div>

      {/* Collapse Button - Bottom Left */}
      <div className="p-4">
        <button
          onClick={toggleSidebar}
          className="flex bg-purple-800 hover:bg-purple-600 rounded-lg items-center justify-center w-8 h-8 text-gray-100 hover:text-white hover:bg-dark-tertiary rounded-lg"
          title="Collapse sidebar (Ctrl+B)"
        >
          <ChevronLeftIcon className="w-5 h-5" />
        </button>
      </div>
    </aside>
  );
}


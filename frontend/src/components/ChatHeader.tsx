import { useChat } from '../context/ChatContext';
import { QuestionMarkCircleIcon } from '@heroicons/react/24/outline';

export default function ChatHeader() {
  const { currentConv, connectionOk } = useChat();

  return (
    <header className="bg-dark-secondary border-b border-dark-tertiary h-20 p-4 flex items-center justify-between">
      <div>
        <h2 className="text-lg font-semibold">
          {currentConv ? currentConv.title : 'Select a conversation or start a new one'}
        </h2>
        <p className="text-sm text-gray-400">AI-powered document chat</p>
      </div>

      <div
        className={`flex items-center gap-2 text-sm ${
          connectionOk ? 'text-green-400' : 'text-red-400'
        }`}
      >
        <div className={`w-2 h-2 rounded-full ${connectionOk ? 'bg-green-400' : 'bg-red-400'}`} />
        {connectionOk ? 'Connected' : 'Disconnected'}
      </div>
    </header>
  );
}

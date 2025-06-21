import { clsx } from 'clsx';

interface Props {
  conv: {
    id: string;
    title: string;
    timestamp: string;
  };
  active?: boolean;
  onClick?: () => void;
}

export default function ConversationItem({ conv, active, onClick }: Props) {
  return (
    <div
      onClick={onClick}
      className={clsx(
        'conversation-item rounded-lg p-3 cursor-pointer truncate',
        active ? 'bg-accent-purple/20 text-white' : 'hover:bg-accent-purple/10 text-gray-300'
      )}
    >
      <p className="text-sm font-medium truncate">{conv.title}</p>
      <p className="text-xs text-gray-400 mt-1">{new Date(conv.timestamp).toLocaleString()}</p>
    </div>
  );
}

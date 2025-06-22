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
        'conversation-item rounded-lg p-4 cursor-pointer truncate bg-black/30 m-4',
        active ? 'bg-purple/20 text-white' : 'hover:bg-purple/10 text-gray-300'
      )}
    >
      <p className="text-sm font-medium truncate">{conv.title}</p>
    </div>
  );
}

import { useChat } from '../context/ChatContext';
import { useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/solid';

export default function NotificationCenter() {
  const { notifications, removeNotification } = useChat();

  /* auto-dismiss after 5 s */
  useEffect(() => {
    const ids = notifications.map(n => setTimeout(() => removeNotification(n.id), 5000));
    return () => ids.forEach(id => clearTimeout(id));
  }, [notifications, removeNotification]);

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {notifications.map(n => (
        <div
          key={n.id}
          className={`${
            n.kind === 'success' ? 'bg-green-600' : 'bg-red-600'
          } text-white px-4 py-3 rounded-lg flex items-start gap-3 shadow-lg max-w-xs`}
        >
          <p className="text-sm flex-1">{n.text}</p>
          <button
            onClick={() => removeNotification(n.id)}
            className="mt-0.5 opacity-70 hover:opacity-100"
          >
            <XMarkIcon className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  );
}

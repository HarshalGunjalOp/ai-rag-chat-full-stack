import Sidebar from './Sidebar.tsx';
import ChatHeader from './ChatHeader.tsx';
import { MessagesList } from './Messages/';
import InputBar from './InputArea/InputBar.tsx';
import { ChatProvider } from '../context/ChatContext.tsx';
import NotificationCenter from './NotificationCenter.tsx';

export default function App() {
  return (
    <ChatProvider>
      <NotificationCenter />
      <div className="flex h-screen bg-slate-900 text-white overflow-hidden">
        <Sidebar />
        <main className="flex-1 flex flex-col">
          <ChatHeader />
          <MessagesList />
          <InputBar />
        </main>
      </div>
    </ChatProvider>
  );
}

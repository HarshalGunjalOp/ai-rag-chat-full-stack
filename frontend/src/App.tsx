
import Sidebar from './components/Sidebar'
import ChatHeader from './components/ChatHeader'
import {MessagesList} from './components/Messages'
import InputBar from './components/InputArea/InputBar'
import {ChatProvider} from './context/ChatContext'
import NotificationCenter from './components/NotificationCenter'
import CollapsedSidebar from './components/CollapsedSidebar' // Import this instead
import {useChat} from './context/ChatContext'

function AppContent() {
  const { sidebarCollapsed } = useChat()
  
  return (
    <>
      <NotificationCenter />
      <div className="flex h-screen bg-slate-800 text-white overflow-hidden relative">
        {/* Render appropriate sidebar based on collapse state */}
        {sidebarCollapsed ? <CollapsedSidebar /> : <Sidebar />}
        
        {/* Main content area - always render */}
        <main className="flex-1 flex flex-col">
          <ChatHeader />
          <MessagesList />
          <InputBar />
        </main>
      </div>
    </>
  )
}

export default function App() {
  return (
    <ChatProvider>
      <AppContent />
    </ChatProvider>
  )
}


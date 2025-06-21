// src/components/InputArea/InputBar.tsx
import {
  PaperAirplaneIcon,
  PaperClipIcon,
  TrashIcon,
  DocumentPlusIcon,
} from '@heroicons/react/24/solid';
import { useState, useRef, useEffect } from 'react';
import { useChat } from '../../context/ChatContext.tsx';
import { useEventSource } from '../../hooks/useEventSource';
import UploadModal from './UploadModal';
import * as api from '../../api/chatApi.ts';

export default function InputBar() {
  const {
    userId,
    addUserMessage,
    pushAssistantPlaceholder,
    appendStreamChunk,
    finaliseAssistant,
    currentConv,
    setLoading,
    isLoading,
    setCurrentConv,
  } = useChat();

  const [text, setText] = useState('');
  const fileInput = useRef<HTMLInputElement>(null);
  const [showUpload, setShowUpload] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const { consume, controllerRef, abort } = useEventSource();
  const [notification, setNotification] = useState<{
    type: 'success' | 'error';
    message: string;
  } | null>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const send = async () => {
    if (!text.trim()) return;
    addUserMessage(text.trim());
    pushAssistantPlaceholder();
    setText('');
    setLoading(true);

    controllerRef.current = new AbortController();
    try {
      const resp = await api.streamMessage(
        userId,
        text.trim(),
        currentConv?.id,
        controllerRef.current.signal
      );
      await consume(
        resp,
        chunk => appendStreamChunk(chunk),
        meta => {
          finaliseAssistant(undefined, meta.sources);
          if (!currentConv) {
            setCurrentConv({
              id: meta.conversationId,
              title: meta.fullText.slice(0, 30),
              timestamp: new Date().toISOString(),
            });
          }
        }
      );
    } catch (err) {
      appendStreamChunk('❌ Error');
    } finally {
      setLoading(false);
    }
  };

  const handleUploadDocuments = () => {
    setShowDropdown(false);
    fileInput.current?.click();
  };

  const handleClearDocuments = async () => {
    setShowDropdown(false);
    try {
      setNotification({ type: 'success', message: 'Clearing documents...' });

      const response = await api.clearDocuments(userId);

      // The response should be a JSON object with a message property
      setNotification({
        type: 'success',
        message: response.ok ? 'Documents cleared successfully!' : 'Failed to clear documents',
      });

      // Refresh document status if you have this function
      // refreshDocStatus();
    } catch (error) {
      console.error('Error clearing documents:', error);
      setNotification({ type: 'error', message: `Failed to clear documents: ${error instanceof Error ? error.message : String(error)}`});
    }

    // Clear notification after 3 seconds
    setTimeout(() => setNotification(null), 3000);
  };

  return (
    <div className="bg-dark-secondary border-t border-dark-tertiary p-4">
      <UploadModal open={showUpload} onClose={() => setShowUpload(false)} />
      <div className="flex items-end gap-3 max-w-4xl mx-auto">
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            className="p-3 text-gray-400 hover:text-white hover:bg-dark-tertiary rounded-lg transition-colors"
          >
            <PaperClipIcon className="w-5 h-5" />
          </button>

          {/* Dropdown Menu */}
          {showDropdown && (
            <div className="absolute bottom-full left-0 mb-4 bg-slate-800 border border-dark-tertiary rounded-lg shadow-lg py-2 min-w-[180px] z-10">
              <button
                onClick={handleUploadDocuments}
                className="w-full px-4 py-2 text-left text-white hover:bg-dark-tertiary flex items-center gap-3 transition-colors"
              >
                <DocumentPlusIcon className="w-4 h-4 text-green-400" />
                Upload Documents
              </button>
              <button
                onClick={handleClearDocuments}
                className="w-full px-4 py-2 text-left text-white hover:bg-dark-tertiary flex items-center gap-3 transition-colors"
              >
                <TrashIcon className="w-4 h-4 text-red-400" />
                Clear All Documents
              </button>
            </div>
          )}
        </div>

        <input
          ref={fileInput}
          type="file"
          multiple
          accept=".pdf,.txt,.md,.jpg,.jpeg,.png,.bmp,.gif"
          hidden
          onChange={e => {
            if (e.target.files?.length) setShowUpload(true);
          }}
        />

        <textarea
          rows={1}
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          placeholder="Type your message..."
          className="flex-1 bg-dark-bg border border-dark-tertiary rounded-lg px-4 py-3 text-white placeholder-gray-400 resize-none focus:ring-2 focus:ring-accent-purple focus:border-transparent"
          style={{ maxHeight: 120 }}
        />

        <button
          disabled={!text.trim() || isLoading}
          onClick={send}
          className="bg-purple-800 hover:bg-purple-600 disabled:bg-gray-700 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg flex gap-2"
        >
          <PaperAirplaneIcon className="w-4 h-4 my-1" />
          Send
        </button>
      </div>
      <p className="text-xs text-gray-500 mt-2 text-center">
        Press Enter to send, Shift+Enter for new line
      </p>
    </div>
  );
}

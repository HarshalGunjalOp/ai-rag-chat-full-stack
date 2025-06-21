// src/components/InputArea/UploadModal.tsx
import { Dialog } from '@headlessui/react';
import { useChat } from '../../context/ChatContext.tsx';
import { useState, useEffect } from 'react';
import * as api from '../../api/chatApi';

export default function UploadModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { userId, refreshDocStatus } = useChat();
  const [files, setFiles] = useState<{ name: string; status: 'uploading' | 'ok' | 'error' }[]>([]);

  useEffect(() => {
    if (!open) return;
    const input = document.querySelector<HTMLInputElement>('input[type=file]')!;
    if (!input.files) return;
    const list = Array.from(input.files);
    setFiles(list.map(f => ({ name: f.name, status: 'uploading' })));

    api
      .uploadFiles(userId, list)
      .then(res => {
        setFiles(
          res.map((r: any) => ({
            name: r.filename,
            status: r.status === 'processing' ? 'ok' : 'error',
          }))
        );
        refreshDocStatus();
      })
      .catch(() => setFiles(list.map(f => ({ name: f.name, status: 'error' }))));
    // eslint-disable-next-line
  }, [open]);

  return (
    <Dialog
      open={open}
      onClose={onClose}
      className="text-white bg-slate-800 fixed inset-0 z-50 flex items-center justify-center bg-black/50"
    >
      <Dialog.Panel className="bg-dark-secondary p-6 rounded-lg max-w-md w-full">
        <Dialog.Title className="text-lg font-semibold text-white mb-4">
          Uploading Documents
        </Dialog.Title>
        <div className="space-y-2 max-h-60 overflow-y-auto pr-2">
          {files.map(f => (
            <div key={f.name} className="flex justify-between bg-dark-tertiary rounded p-2">
              <span className="truncate">{f.name}</span>
              {f.status === 'uploading' && <span className="animate-spin">⏳</span>}
              {f.status === 'ok' && <span className="text-green-400">✔</span>}
              {f.status === 'error' && <span className="text-red-400">✖</span>}
            </div>
          ))}
        </div>
        <button
          className="mt-4 bg-purple-800 hover:bg-purple-600 text-white px-4 py-2 rounded-lg"
          onClick={onClose}
        >
          Close
        </button>
      </Dialog.Panel>
    </Dialog>
  );
}

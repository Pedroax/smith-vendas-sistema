'use client';

import { useState, useRef, ChangeEvent } from 'react';
import { Upload, File as FileIcon, Loader2, CheckCircle2, X, AlertCircle } from 'lucide-react';

type UploadState = 'idle' | 'selected' | 'uploading' | 'success' | 'error';

interface FileUploadProps {
  onUpload: (file: File) => Promise<void>;
  accept?: string;
  maxSizeMB?: number;
  label?: string;
  className?: string;
}

export function FileUpload({
  onUpload,
  accept = '*',
  maxSizeMB = 50,
  label = 'Enviar Arquivo',
  className = '',
}: FileUploadProps) {
  const [state, setState] = useState<UploadState>('idle');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string>('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const handleFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file size
    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      setError(`Arquivo muito grande. Máximo: ${maxSizeMB}MB`);
      setState('error');
      return;
    }

    setSelectedFile(file);
    setState('selected');
    setError('');
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setState('uploading');
    setUploadProgress(0);
    setError('');

    try {
      // Simulate progress (you can enhance this with actual upload progress)
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 100);

      await onUpload(selectedFile);

      clearInterval(progressInterval);
      setUploadProgress(100);
      setState('success');

      // Reset after 2 seconds
      setTimeout(() => {
        setState('idle');
        setSelectedFile(null);
        setUploadProgress(0);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      }, 2000);
    } catch (err: any) {
      setState('error');
      setError(err.message || 'Erro ao enviar arquivo');
      setUploadProgress(0);
    }
  };

  const handleCancel = () => {
    setState('idle');
    setSelectedFile(null);
    setError('');
    setUploadProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className={className}>
      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        onChange={handleFileSelect}
        className="hidden"
        id="file-upload-input"
      />

      {state === 'idle' && (
        <label
          htmlFor="file-upload-input"
          className="flex items-center justify-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-colors cursor-pointer text-sm font-medium"
        >
          <Upload className="w-4 h-4" />
          {label}
        </label>
      )}

      {state === 'selected' && selectedFile && (
        <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl border border-gray-200">
          <FileIcon className="w-5 h-5 text-gray-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">{selectedFile.name}</p>
            <p className="text-xs text-gray-500">{formatFileSize(selectedFile.size)}</p>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              onClick={handleUpload}
              className="px-3 py-1.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-xs font-medium"
            >
              Enviar
            </button>
            <button
              onClick={handleCancel}
              className="p-1.5 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {state === 'uploading' && selectedFile && (
        <div className="p-3 bg-blue-50 rounded-xl border border-blue-200">
          <div className="flex items-center gap-3 mb-2">
            <Loader2 className="w-5 h-5 text-blue-600 animate-spin flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">{selectedFile.name}</p>
              <p className="text-xs text-gray-500">Enviando... {uploadProgress}%</p>
            </div>
          </div>
          <div className="w-full h-1.5 bg-blue-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600 transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      {state === 'success' && selectedFile && (
        <div className="flex items-center gap-3 p-3 bg-green-50 rounded-xl border border-green-200">
          <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-medium text-green-900">Arquivo enviado com sucesso!</p>
            <p className="text-xs text-green-600">{selectedFile.name}</p>
          </div>
        </div>
      )}

      {state === 'error' && (
        <div className="flex items-start gap-3 p-3 bg-red-50 rounded-xl border border-red-200">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-red-900">Erro no envio</p>
            <p className="text-xs text-red-600">{error}</p>
          </div>
          <button
            onClick={handleCancel}
            className="p-1 text-red-400 hover:text-red-600 transition-colors flex-shrink-0"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}

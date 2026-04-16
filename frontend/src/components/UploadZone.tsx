"use client";
import { useState, useRef } from "react";
import api from "@/lib/axios";
import { useRouter } from "next/navigation";

export default function UploadZone() {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const upload = async (file: File) => {
    if (!file.name.endsWith(".pdf")) {
      setError("Only PDF files are supported");
      return;
    }
    setError("");
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const { data } = await api.post("/documents/upload", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      // Tell sidebar to refresh
      window.dispatchEvent(new Event("doc:uploaded"));
      // Go straight to the chat page for this doc
      router.push(`/dashboard/chat/${data.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) upload(file);
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) upload(file);
  };

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      onClick={() => !uploading && inputRef.current?.click()}
      className={`
        border-2 border-dashed rounded-2xl p-16 flex flex-col items-center justify-center
        cursor-pointer transition-all select-none
        ${dragging ? "border-gray-400 bg-gray-100" : "border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50"}
        ${uploading ? "pointer-events-none opacity-60" : ""}
      `}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        className="hidden"
        onChange={onFileChange}
      />

      {uploading ? (
        <>
          <div className="w-8 h-8 border-2 border-gray-300 border-t-gray-900 rounded-full animate-spin mb-4" />
          <p className="text-sm font-medium text-gray-700">Uploading...</p>
          <p className="text-xs text-gray-400 mt-1">Embedding will start automatically</p>
        </>
      ) : (
        <>
          <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mb-4">
            <svg className="w-6 h-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <p className="text-sm font-medium text-gray-700">Drop a PDF here</p>
          <p className="text-xs text-gray-400 mt-1">or click to browse</p>
        </>
      )}

      {error && <p className="text-xs text-red-500 mt-4">{error}</p>}
    </div>
  );
}
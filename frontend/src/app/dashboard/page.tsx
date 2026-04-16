"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/axios";
import { Document } from "@/types/document";
import UploadZone from "@/components/UploadZone";
import StatusPoller from "@/components/StatusPoller";

const statusStyles: Record<Document["status"], string> = {
  ready: "bg-green-50 text-green-700 border-green-200",
  processing: "bg-yellow-50 text-yellow-700 border-yellow-200",
  pending: "bg-yellow-50 text-yellow-700 border-yellow-200",
  failed: "bg-red-50 text-red-700 border-red-200",
};

export default function DashboardPage() {
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const fetchDocs = async () => {
    try {
      const { data } = await api.get("/documents/?page=1&page_size=50");
      setDocs(data.items);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
    window.addEventListener("doc:uploaded", fetchDocs);
    return () => window.removeEventListener("doc:uploaded", fetchDocs);
  }, []);

  const deleteDoc = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (!confirm("Delete this document?")) return;
    await api.delete(`/documents/${id}`);
    setDocs((prev) => prev.filter((d) => d.id !== id));
  };

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-6 h-6 border-2 border-gray-200 border-t-gray-900 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-xl font-semibold text-gray-900">Documents</h1>
        <p className="text-sm text-gray-500 mt-1">Upload a PDF to start chatting with it</p>
      </div>

      <UploadZone />

      {docs.length > 0 && (
        <div className="mt-8">
          <h2 className="text-sm font-medium text-gray-500 mb-3">Your documents</h2>
          <div className="grid grid-cols-1 gap-3">
            {docs.map((doc) => (
              <div key={doc.id}>
                {/* Poll status for non-ready docs */}
                {(doc.status === "pending" || doc.status === "processing") && (
                  <StatusPoller
                    docId={doc.id}
                    currentStatus={doc.status}
                    onReady={fetchDocs}
                  />
                )}
                <div
                  onClick={() => doc.status === "ready" && router.push(`/dashboard/chat/${doc.id}`)}
                  className={`
                    flex items-center justify-between p-4 bg-white border border-gray-200
                    rounded-xl transition
                    ${doc.status === "ready" ? "cursor-pointer hover:border-gray-300 hover:shadow-sm" : ""}
                  `}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-9 h-9 bg-gray-100 rounded-lg flex items-center justify-center shrink-0">
                      <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{doc.filename}</p>
                      <p className="text-xs text-gray-400">{formatDate(doc.created_at)}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0 ml-4">
                    <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${statusStyles[doc.status]}`}>
                      {doc.status}
                    </span>
                    <button
                      onClick={(e) => deleteDoc(e, doc.id)}
                      className="text-gray-300 hover:text-red-400 transition text-lg leading-none"
                    >
                      ×
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
"use client";
import { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import api from "@/lib/axios";
import { Document } from "@/types/document";

export default function Sidebar() {
  const [docs, setDocs] = useState<Document[]>([]);
  const router = useRouter();
  const params = useParams();
  const activeId = params?.docId as string;

  const fetchDocs = useCallback(async () => {
    try {
      const { data } = await api.get("/documents/?page=1&page_size=50");
      setDocs(data.items);
    } catch {}
  }, []);

  useEffect(() => {
    fetchDocs();
  }, [fetchDocs]);

  // Re-fetch when a new doc is uploaded (custom event)
  useEffect(() => {
    window.addEventListener("doc:uploaded", fetchDocs);
    return () => window.removeEventListener("doc:uploaded", fetchDocs);
  }, [fetchDocs]);

  const statusDot = (status: Document["status"]) => {
    const colors: Record<Document["status"], string> = {
      ready: "bg-green-400",
      processing: "bg-yellow-400 animate-pulse",
      pending: "bg-yellow-400 animate-pulse",
      failed: "bg-red-400",
    };
    return <span className={`w-2 h-2 rounded-full shrink-0 ${colors[status]}`} />;
  };

  return (
    <aside className="w-64 border-r border-gray-200 bg-white flex flex-col shrink-0 overflow-hidden">
      <div className="p-4 border-b border-gray-100">
        <button
          onClick={() => router.push("/dashboard")}
          className="w-full text-left text-sm font-medium text-gray-700 hover:text-gray-900 transition"
        >
          + Upload document
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {docs.length === 0 ? (
          <p className="text-xs text-gray-400 text-center mt-8 px-4">
            No documents yet
          </p>
        ) : (
          <ul className="py-2">
            {docs.map((doc) => (
              <li key={doc.id}>
                <button
                  onClick={() => router.push(`/dashboard/chat/${doc.id}`)}
                  className={`w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-gray-50 transition ${
                    activeId === doc.id ? "bg-gray-100" : ""
                  }`}
                >
                  {statusDot(doc.status)}
                  <span className="text-sm text-gray-700 truncate">{doc.filename}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
}
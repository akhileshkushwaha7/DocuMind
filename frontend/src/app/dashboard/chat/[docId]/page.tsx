"use client";
import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import api from "@/lib/axios";
import { Message } from "@/types/chat";
import { Document } from "@/types/document";
import MessageList from "@/components/chat/MessageList";
import ChatInput from "@/components/chat/ChatInput";
import StatusBanner from "@/components/chat/StatusBanner";
import StatusPoller from "@/components/StatusPoller";

export default function ChatPage() {
  const { docId } = useParams() as { docId: string };

  const [doc, setDoc] = useState<Document | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [streamingContent, setStreamingContent] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchDoc = useCallback(async () => {
    const { data } = await api.get(`/documents/${docId}`);
    setDoc(data);
  }, [docId]);

  const fetchHistory = useCallback(async () => {
    const { data } = await api.get(`/chat/${docId}/history`);
    setMessages(data);
  }, [docId]);

  useEffect(() => {
    const init = async () => {
      try {
        await fetchDoc();
        await fetchHistory();
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [fetchDoc, fetchHistory]);

  const sendMessage = async (text: string) => {
    if (!doc || doc.status !== "ready") return;

    // Optimistically add user message to UI
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsTyping(true);
    setStreamingContent("");

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/chat/${docId}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("access_token")}`,
          },
          body: JSON.stringify({ message: text }),
        }
      );

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Request failed");
      }

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let fullContent = "";

      setIsTyping(false);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const raw = line.slice(6).trim();
          if (!raw) continue;

          try {
            const parsed = JSON.parse(raw);

            if (parsed.token) {
              fullContent += parsed.token;
              setStreamingContent(fullContent);
            }

            if (parsed.done) {
              // Streaming finished — commit to messages list
              const assistantMsg: Message = {
                id: crypto.randomUUID(),
                role: "assistant",
                content: fullContent,
                created_at: new Date().toISOString(),
              };
              setMessages((prev) => [...prev, assistantMsg]);
              setStreamingContent("");
            }

            if (parsed.error) {
              throw new Error(parsed.error);
            }
          } catch {}
        }
      }
    } catch (err: any) {
      setIsTyping(false);
      setStreamingContent("");
      const errMsg: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: `Error: ${err.message || "Something went wrong"}`,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errMsg]);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-6 h-6 border-2 border-gray-200 border-t-gray-900 rounded-full animate-spin" />
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-sm text-gray-500">Document not found</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-gray-50 rounded-2xl overflow-hidden border border-gray-200">

      {/* Header */}
      <div className="border-b border-gray-200 bg-white px-6 py-4 shrink-0">
        <p className="text-sm font-medium text-gray-900 truncate">{doc.filename}</p>
        <p className="text-xs text-gray-400 mt-0.5">
          {doc.status === "ready" ? "Ready to chat" : `Status: ${doc.status}`}
        </p>
      </div>

      {/* Status banner for non-ready docs */}
      {doc.status !== "ready" && (
        <>
          <StatusBanner status={doc.status} />
          <StatusPoller
            docId={doc.id}
            currentStatus={doc.status}
            onReady={fetchDoc}
          />
        </>
      )}

      {/* Messages */}
      <MessageList
        messages={messages}
        streamingContent={streamingContent}
        isTyping={isTyping}
      />

      {/* Input */}
      <ChatInput
        onSend={sendMessage}
        disabled={doc.status !== "ready" || isTyping || streamingContent !== ""}
      />
    </div>
  );
}
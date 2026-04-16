"use client";
import { useEffect, useRef } from "react";
import { Message } from "@/types/chat";
import MessageBubble from "./MessageBubble";
import TypingIndicator from "./TypingIndicator";

interface Props {
  messages: Message[];
  streamingContent: string;
  isTyping: boolean;
}

export default function MessageList({ messages, streamingContent, isTyping }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto scroll to bottom on new messages or tokens
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent, isTyping]);

  const streamingMessage: Message = {
    id: "streaming",
    role: "assistant",
    content: streamingContent,
    created_at: new Date().toISOString(),
  };

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6">
      {messages.length === 0 && !isTyping && (
        <div className="flex flex-col items-center justify-center h-full text-center">
          <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mb-3">
            <svg className="w-6 h-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          </div>
          <p className="text-sm font-medium text-gray-700">Ask anything about this document</p>
          <p className="text-xs text-gray-400 mt-1">The AI will answer based only on the document content</p>
        </div>
      )}

      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}

      {/* Show typing dots before first token arrives */}
      {isTyping && streamingContent === "" && <TypingIndicator />}

      {/* Stream tokens into a live bubble */}
      {streamingContent && (
        <MessageBubble message={streamingMessage} isStreaming={true} />
      )}

      <div ref={bottomRef} />
    </div>
  );
}
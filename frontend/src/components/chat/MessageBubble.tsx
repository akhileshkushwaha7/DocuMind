import { Message } from "@/types/chat";

interface Props {
  message: Message;
  isStreaming?: boolean;
}

export default function MessageBubble({ message, isStreaming }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-gray-900 flex items-center justify-center shrink-0 mr-3 mt-0.5">
          <span className="text-white text-xs font-bold">D</span>
        </div>
      )}

      <div
        className={`
          max-w-[70%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed
          ${isUser
            ? "bg-gray-900 text-white rounded-tr-sm"
            : "bg-white border border-gray-200 text-gray-800 rounded-tl-sm"
          }
        `}
      >
        {message.content}
        {isStreaming && (
          <span className="inline-block w-1.5 h-4 bg-gray-400 ml-0.5 align-middle animate-pulse rounded-sm" />
        )}
      </div>

      {isUser && (
        <div className="w-7 h-7 rounded-full bg-gray-100 flex items-center justify-center shrink-0 ml-3 mt-0.5">
          <span className="text-gray-600 text-xs font-medium">U</span>
        </div>
      )}
    </div>
  );
}
import { Document } from "@/types/document";

interface Props {
  status: Document["status"];
}

const config = {
  pending: {
    text: "Document is queued for embedding...",
    sub: "This usually takes under a minute",
    style: "bg-yellow-50 border-yellow-200 text-yellow-800",
    dot: "bg-yellow-400 animate-pulse",
  },
  processing: {
    text: "Embedding document...",
    sub: "Reading and indexing your PDF",
    style: "bg-yellow-50 border-yellow-200 text-yellow-800",
    dot: "bg-yellow-400 animate-pulse",
  },
  failed: {
    text: "Embedding failed",
    sub: "Try uploading the document again",
    style: "bg-red-50 border-red-200 text-red-800",
    dot: "bg-red-400",
  },
  ready: null,
};

export default function StatusBanner({ status }: Props) {
  const cfg = config[status];
  if (!cfg) return null;

  return (
    <div className={`mx-6 mt-4 flex items-center gap-3 px-4 py-3 rounded-xl border ${cfg.style}`}>
      <span className={`w-2 h-2 rounded-full shrink-0 ${cfg.dot}`} />
      <div>
        <p className="text-sm font-medium">{cfg.text}</p>
        <p className="text-xs opacity-70 mt-0.5">{cfg.sub}</p>
      </div>
    </div>
  );
}
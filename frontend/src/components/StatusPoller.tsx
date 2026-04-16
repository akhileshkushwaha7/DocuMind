"use client";
import { useEffect } from "react";
import api from "@/lib/axios";

interface Props {
  docId: string;
  currentStatus: string;
  onReady: () => void;
}

export default function StatusPoller({ docId, currentStatus, onReady }: Props) {
  useEffect(() => {
    if (currentStatus === "ready" || currentStatus === "failed") return;

    const interval = setInterval(async () => {
      try {
        const { data } = await api.get(`/documents/${docId}/status`);
        if (data.status === "ready" || data.status === "failed") {
          clearInterval(interval);
          onReady();
        }
      } catch {
        clearInterval(interval);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [docId, currentStatus, onReady]);

  return null;
}
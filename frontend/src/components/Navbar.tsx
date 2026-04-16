"use client";
import { useAuth } from "@/context/AuthContext";
import Link from "next/link";

export default function Navbar() {
  const { user, logout } = useAuth();

  return (
    <header className="h-14 border-b border-gray-200 bg-white flex items-center justify-between px-6 shrink-0">
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 bg-gray-900 rounded-lg flex items-center justify-center">
          <span className="text-white text-xs font-bold">D</span>
        </div>
        <span className="font-semibold text-gray-900 text-sm">DocuMind</span>
      </div>

      <div className="flex items-center gap-4">
        {user?.role === "admin" && (
          <Link
            href="/dashboard/admin"
            className="text-sm text-gray-500 hover:text-gray-900 transition"
          >
            Admin
          </Link>
        )}
        <span className="text-sm text-gray-500">{user?.email}</span>
        <button
          onClick={logout}
          className="text-sm text-gray-500 hover:text-gray-900 transition"
        >
          Sign out
        </button>
      </div>
    </header>
  );
}
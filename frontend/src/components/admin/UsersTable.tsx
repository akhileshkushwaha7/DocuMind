"use client";
import { useState } from "react";
import { AdminUser } from "@/types/admin";

interface Props {
  users: AdminUser[];
  total: number;
  page: number;
  onPageChange: (p: number) => void;
  onSearch: (q: string) => void;
}

export default function UsersTable({ users, total, page, onPageChange, onSearch }: Props) {
  const [search, setSearch] = useState("");
  const pageSize = 20;
  const totalPages = Math.ceil(total / pageSize);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
    onSearch(e.target.value);
  };

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString("en-US", {
      month: "short", day: "numeric", year: "numeric",
    });

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      {/* Table header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
        <p className="text-sm font-medium text-gray-900">
          Users
          <span className="text-gray-400 font-normal ml-2">{total}</span>
        </p>
        <input
          type="text"
          value={search}
          onChange={handleSearch}
          placeholder="Search by email..."
          className="text-sm px-3 py-1.5 border border-gray-200 rounded-lg outline-none focus:border-gray-400 transition w-56"
        />
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500">Email</th>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500">Role</th>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500">Documents</th>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500">Joined</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id} className="border-b border-gray-50 hover:bg-gray-50 transition">
                <td className="px-5 py-3 text-gray-900">{user.email}</td>
                <td className="px-5 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium border ${
                    user.role === "admin"
                      ? "bg-purple-50 text-purple-700 border-purple-200"
                      : "bg-gray-50 text-gray-600 border-gray-200"
                  }`}>
                    {user.role}
                  </span>
                </td>
                <td className="px-5 py-3 text-gray-600">{user.doc_count}</td>
                <td className="px-5 py-3 text-gray-400">{formatDate(user.created_at)}</td>
              </tr>
            ))}
            {users.length === 0 && (
              <tr>
                <td colSpan={4} className="px-5 py-10 text-center text-gray-400 text-sm">
                  No users found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-5 py-3 border-t border-gray-100">
          <p className="text-xs text-gray-400">
            Page {page} of {totalPages}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page === 1}
              className="text-xs px-3 py-1.5 border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50 transition"
            >
              Previous
            </button>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page === totalPages}
              className="text-xs px-3 py-1.5 border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50 transition"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
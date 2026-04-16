"use client";
import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/axios";
import { AdminStats, AdminUser } from "@/types/admin";
import StatsCards from "@/components/admin/StatsCards";
import UploadsChart from "@/components/admin/UploadsChart";
import UsersTable from "@/components/admin/UsersTable";

export default function AdminPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  // Redirect non-admins
  useEffect(() => {
    if (user && user.role !== "admin") {
      router.push("/dashboard");
    }
  }, [user, router]);

  const fetchStats = useCallback(async () => {
    const { data } = await api.get("/admin/stats");
    setStats(data);
  }, []);

  const fetchUsers = useCallback(async () => {
    const { data } = await api.get(
      `/admin/users?page=${page}&page_size=20&search=${search}`
    );
    setUsers(data.items);
    setTotal(data.total);
  }, [page, search]);

  useEffect(() => {
    const init = async () => {
      try {
        await Promise.all([fetchStats(), fetchUsers()]);
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [fetchStats, fetchUsers]);

  // Debounce search
  useEffect(() => {
    const t = setTimeout(() => fetchUsers(), 300);
    return () => clearTimeout(t);
  }, [search, fetchUsers]);

  if (loading || !stats) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-6 h-6 border-2 border-gray-200 border-t-gray-900 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Admin</h1>
        <p className="text-sm text-gray-500 mt-1">Platform overview</p>
      </div>

      <StatsCards stats={stats} />
      <UploadsChart data={stats.uploads_by_day} />
      <UsersTable
        users={users}
        total={total}
        page={page}
        onPageChange={setPage}
        onSearch={setSearch}
      />
    </div>
  );
}
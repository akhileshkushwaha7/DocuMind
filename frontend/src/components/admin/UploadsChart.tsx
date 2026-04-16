"use client";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

interface Props {
  data: { date: string; count: number }[];
}

const formatDate = (date: string) => {
  const d = new Date(date);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-gray-200 rounded-lg px-3 py-2 text-sm shadow-sm">
      <p className="text-gray-500">{formatDate(label)}</p>
      <p className="font-semibold text-gray-900 mt-0.5">{payload[0].value} uploads</p>
    </div>
  );
};

export default function UploadsChart({ data }: Props) {
  const formatDate = (date: string) => {
    return new Date(date + "T00:00:00").toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;

    return (
      <div className="bg-white border border-gray-200 rounded-lg px-3 py-2 text-sm shadow-sm">
        <p className="text-gray-500">{formatDate(label)}</p>
        <p className="font-semibold text-gray-900 mt-0.5">
          {payload[0].value} uploads
        </p>
      </div>
    );
  };

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <p className="text-sm font-medium text-gray-900 mb-4">
        Uploads — last 30 days
      </p>

      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} barSize={14}>
          <CartesianGrid vertical={false} stroke="#f0f0f0" />

          <XAxis
            dataKey="date"
            tickFormatter={(date) => formatDate(date)}
            tick={{ fontSize: 11, fill: "#9ca3af" }}
            axisLine={false}
            tickLine={false}
          />

          <YAxis
            allowDecimals={false}
            tick={{ fontSize: 11, fill: "#9ca3af" }}
            axisLine={false}
            tickLine={false}
            width={24}
          />

          <Tooltip content={<CustomTooltip />} cursor={{ fill: "#f9fafb" }} />

          <Bar dataKey="count" fill="#111827" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

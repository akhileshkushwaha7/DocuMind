import { AdminStats } from "@/types/admin";

interface Props {
  stats: AdminStats;
}

const cards = (stats: AdminStats) => [
  { label: "Total users", value: stats.total_users },
  { label: "Total documents", value: stats.total_docs },
  { label: "Total messages", value: stats.total_messages },
];

export default function StatsCards({ stats }: Props) {
  return (
    <div className="grid grid-cols-3 gap-4">
      {cards(stats).map((card) => (
        <div
          key={card.label}
          className="bg-white border border-gray-200 rounded-xl p-5"
        >
          <p className="text-xs text-gray-500 font-medium">{card.label}</p>
          <p className="text-3xl font-semibold text-gray-900 mt-1">
            {card.value.toLocaleString()}
          </p>
        </div>
      ))}
    </div>
  );
}
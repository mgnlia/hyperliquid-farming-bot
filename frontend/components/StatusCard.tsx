"use client";

interface StatusCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  color?: "green" | "blue" | "yellow" | "red" | "purple";
}

const colorMap = {
  green: "border-green-500 text-green-400",
  blue: "border-blue-500 text-blue-400",
  yellow: "border-yellow-500 text-yellow-400",
  red: "border-red-500 text-red-400",
  purple: "border-purple-500 text-purple-400",
};

export function StatusCard({ title, value, subtitle, color = "blue" }: StatusCardProps) {
  return (
    <div className={`bg-gray-900 border-l-4 ${colorMap[color]} rounded-lg p-4`}>
      <p className="text-xs text-gray-400 uppercase tracking-wide">{title}</p>
      <p className={`text-2xl font-bold mt-1 ${colorMap[color].split(" ")[1]}`}>{value}</p>
      {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
    </div>
  );
}

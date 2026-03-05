"use client";

interface StatusCardProps {
  title: string;
  value: string;
  note?: string;
  tone?: "blue" | "green" | "yellow" | "red";
}

const toneStyles: Record<NonNullable<StatusCardProps["tone"]>, string> = {
  blue: "border-blue-500 text-blue-300",
  green: "border-green-500 text-green-300",
  yellow: "border-yellow-500 text-yellow-300",
  red: "border-red-500 text-red-300",
};

export function StatusCard({ title, value, note, tone = "blue" }: StatusCardProps) {
  return (
    <div className={`rounded-xl border ${toneStyles[tone]} bg-slate-950/70 p-4`}>
      <p className="text-xs uppercase tracking-wider text-slate-400">{title}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
      {note ? <p className="mt-2 text-xs text-slate-500">{note}</p> : null}
    </div>
  );
}

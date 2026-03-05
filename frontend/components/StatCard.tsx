'use client'
interface Props {
  label: string
  value: string | number
  sub?: string
  color?: 'green' | 'red' | 'blue' | 'yellow' | 'purple' | 'default'
}
const colorMap = {
  green: 'text-[#00d4a0]',
  red: 'text-[#ef4444]',
  blue: 'text-[#3b82f6]',
  yellow: 'text-[#f59e0b]',
  purple: 'text-[#8b5cf6]',
  default: 'text-[#e5e7eb]',
}
export default function StatCard({ label, value, sub, color = 'default' }: Props) {
  return (
    <div className="card flex flex-col gap-1">
      <div className="text-[#6b7280] text-xs font-medium uppercase tracking-wide">{label}</div>
      <div className={`text-2xl font-bold ${colorMap[color]}`}>{value}</div>
      {sub && <div className="text-[#6b7280] text-xs">{sub}</div>}
    </div>
  )
}

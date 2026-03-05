'use client'
import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { api } from '@/lib/api'

export default function PnLChart() {
  const [chartData, setChartData] = useState<any[]>([])

  useEffect(() => {
    async function buildChart() {
      try {
        const { trades } = await api.trades(100)
        if (!trades?.length) return
        let cumVol = 0
        const points = trades.slice().reverse().map((t: any, i: number) => {
          cumVol += t.usd_value || 0
          return {
            i: i + 1,
            volume: Math.round(cumVol),
            time: new Date(t.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          }
        })
        setChartData(points)
      } catch {}
    }
    buildChart()
    const t = setInterval(buildChart, 20000)
    return () => clearInterval(t)
  }, [])

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload?.length) {
      return (
        <div className="bg-[#111827] border border-[#1f2937] rounded-lg p-3 text-sm">
          <div className="text-[#6b7280] text-xs">{payload[0]?.payload?.time}</div>
          <div className="text-[#3b82f6] font-bold">${payload[0]?.value?.toLocaleString()}</div>
          <div className="text-[#6b7280] text-xs">cumulative volume</div>
        </div>
      )
    }
    return null
  }

  return (
    <div className="card flex flex-col gap-4">
      <h2 className="text-lg font-bold">📈 Cumulative Volume</h2>
      {chartData.length === 0 ? (
        <div className="h-40 flex items-center justify-center text-[#6b7280] text-sm">
          Waiting for trades...
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={180}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="time" tick={{ fill: '#6b7280', fontSize: 10 }} tickLine={false} axisLine={false} />
            <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={v => `$${v}`} />
            <Tooltip content={<CustomTooltip />} />
            <Line type="monotone" dataKey="volume" stroke="#3b82f6" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}

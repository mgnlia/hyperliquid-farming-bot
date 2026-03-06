"use client";

import { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

import { api } from "@/lib/api";

export default function PnLChart() {
  const [chartData, setChartData] = useState<Array<Record<string, unknown>>>([]);

  useEffect(() => {
    async function buildChart() {
      try {
        const { trades } = await api.trades(100);
        if (!trades?.length) {
          return;
        }

        let cumVol = 0;
        const points = trades
          .slice()
          .reverse()
          .map((t, i) => {
            cumVol += Number(t.usd_value ?? t.size ?? 0);
            return {
              i: i + 1,
              volume: Math.round(cumVol),
              time: new Date((t.created_at ? Date.parse(t.created_at) : Number(t.timestamp) * 1000) || Date.now()).toLocaleTimeString(
                [],
                {
                  hour: "2-digit",
                  minute: "2-digit",
                }
              ),
            };
          });

        setChartData(points);
      } catch {
        // ignore chart refresh errors
      }
    }

    void buildChart();
    const timer = setInterval(() => {
      void buildChart();
    }, 20000);

    return () => clearInterval(timer);
  }, []);

  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{ value?: number; payload?: { time?: string } }> }) => {
    if (active && payload?.length) {
      return (
        <div className="rounded-lg border border-[#1f2937] bg-[#111827] p-3 text-sm">
          <div className="text-xs text-[#6b7280]">{payload[0]?.payload?.time}</div>
          <div className="font-bold text-[#3b82f6]">${payload[0]?.value?.toLocaleString()}</div>
          <div className="text-xs text-[#6b7280]">cumulative volume</div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="card flex flex-col gap-4 rounded-xl border border-slate-800 bg-slate-950/70 p-4">
      <h2 className="text-lg font-bold">📈 Cumulative Volume</h2>
      {chartData.length === 0 ? (
        <div className="flex h-40 items-center justify-center text-sm text-[#6b7280]">Waiting for trades...</div>
      ) : (
        <ResponsiveContainer width="100%" height={180}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="time" tick={{ fill: "#6b7280", fontSize: 10 }} tickLine={false} axisLine={false} />
            <YAxis
              tick={{ fill: "#6b7280", fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v: number) => `$${v}`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line type="monotone" dataKey="volume" stroke="#3b82f6" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

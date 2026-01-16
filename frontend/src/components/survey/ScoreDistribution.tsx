"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ScoreDistributionProps {
  distribution: Record<string, number>;
}

export function ScoreDistribution({ distribution }: ScoreDistributionProps) {
  const data = Object.entries(distribution)
    .map(([range, count]) => ({
      range,
      count,
      start: parseFloat(range.split("-")[0]),
    }))
    .sort((a, b) => a.start - b.start);

  const getBarColor = (start: number) => {
    if (start >= 0.7) return "#22c55e";
    if (start >= 0.5) return "#eab308";
    if (start >= 0.3) return "#f97316";
    return "#ef4444";
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Score Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="range"
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={60}
              />
              <YAxis allowDecimals={false} />
              <Tooltip
                formatter={(value) => [`${Number(value)} respondents`, "Count"]}
                labelFormatter={(label) => `Score Range: ${label}`}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getBarColor(entry.start)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

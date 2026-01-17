"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, Target } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from "recharts";
import type { KeyDriver } from "@/lib/types";

interface KeyDriversChartProps {
  keyDrivers: KeyDriver[];
}

export function KeyDriversChart({ keyDrivers }: KeyDriversChartProps) {
  // Sort by absolute correlation value
  const sortedDrivers = [...keyDrivers]
    .sort((a, b) => Math.abs(b.correlation) - Math.abs(a.correlation))
    .slice(0, 10);

  const chartData = sortedDrivers.map((driver) => ({
    name: driver.factor.length > 15 ? driver.factor.slice(0, 15) + "..." : driver.factor,
    fullName: driver.factor,
    correlation: driver.correlation,
    impact: driver.impact,
    evidenceCount: driver.evidence_count,
    description: driver.description,
  }));

  const positiveCount = keyDrivers.filter((d) => d.impact === "positive").length;
  const negativeCount = keyDrivers.filter((d) => d.impact === "negative").length;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Target className="h-5 w-5 text-blue-500" />
            <CardTitle>Key Drivers Analysis</CardTitle>
          </div>
          <div className="flex gap-2">
            <Badge variant="outline" className="text-green-600 border-green-600">
              <TrendingUp className="h-3 w-3 mr-1" />
              {positiveCount} 긍정
            </Badge>
            <Badge variant="outline" className="text-red-600 border-red-600">
              <TrendingDown className="h-3 w-3 mr-1" />
              {negativeCount} 부정
            </Badge>
          </div>
        </div>
        <CardDescription>
          구매 의도(SSR 점수)에 영향을 미치는 핵심 요인 분석
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-[400px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
              <XAxis
                type="number"
                domain={[-1, 1]}
                tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
              />
              <YAxis
                type="category"
                dataKey="name"
                width={120}
                tick={{ fontSize: 12 }}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <div className="bg-white p-3 border rounded-lg shadow-lg max-w-xs">
                        <p className="font-medium">{data.fullName}</p>
                        <p className="text-sm text-muted-foreground mt-1">
                          상관관계: {(data.correlation * 100).toFixed(1)}%
                        </p>
                        <p className="text-sm text-muted-foreground">
                          영향: {data.impact === "positive" ? "긍정적" : "부정적"}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          근거 수: {data.evidenceCount}건
                        </p>
                        {data.description && (
                          <p className="text-xs text-muted-foreground mt-2 border-t pt-2">
                            {data.description.slice(0, 100)}...
                          </p>
                        )}
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <ReferenceLine x={0} stroke="#888" strokeDasharray="3 3" />
              <Bar dataKey="correlation" radius={[0, 4, 4, 0]}>
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.impact === "positive" ? "#22c55e" : "#ef4444"}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Driver Details */}
        <div className="mt-6 space-y-3">
          <h4 className="text-sm font-medium">상세 요인 분석</h4>
          <div className="grid gap-2">
            {sortedDrivers.slice(0, 5).map((driver, index) => (
              <div
                key={index}
                className={`p-3 rounded-lg border ${
                  driver.impact === "positive"
                    ? "bg-green-50 border-green-200"
                    : "bg-red-50 border-red-200"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {driver.impact === "positive" ? (
                      <TrendingUp className="h-4 w-4 text-green-600" />
                    ) : (
                      <TrendingDown className="h-4 w-4 text-red-600" />
                    )}
                    <span className="font-medium text-sm">{driver.factor}</span>
                  </div>
                  <Badge variant="secondary">
                    {(driver.correlation * 100).toFixed(0)}%
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {driver.description.slice(0, 80)}
                  {driver.description.length > 80 && "..."}
                </p>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

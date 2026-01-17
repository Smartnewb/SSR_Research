"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertCircle } from "lucide-react";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { PainPoint, QIEAggregatedStats } from "@/lib/types";

interface PainPointRadarProps {
  painPoints: PainPoint[];
  aggregatedStats: QIEAggregatedStats;
}

const CATEGORY_LABELS: Record<string, string> = {
  Price: "가격",
  UX: "사용성",
  Trust: "신뢰",
  Feature: "기능",
  Convenience: "편의성",
  Other: "기타",
};

export function PainPointRadar({ painPoints, aggregatedStats }: PainPointRadarProps) {
  // Build radar data from category stats
  const categoryStats = aggregatedStats.category_stats || [];

  // Create radar data with 5 main categories
  const radarCategories = ["Price", "UX", "Trust", "Feature", "Convenience"];

  const radarData = radarCategories.map((cat) => {
    const stat = categoryStats.find((s) => s.category === cat);
    const painPoint = painPoints.find((p) => p.category === cat);

    // Calculate severity from pain points or inverse of avg_ssr
    let severity = 0;
    if (painPoint) {
      severity = painPoint.score;
    } else if (stat && stat.avg_ssr < 0.5) {
      severity = (1 - stat.avg_ssr) * 100;
    }

    return {
      category: CATEGORY_LABELS[cat] || cat,
      fullCategory: cat,
      severity: Math.min(100, Math.max(0, severity)),
      count: stat?.count || 0,
      avgSSR: stat?.avg_ssr || 0,
      percentage: stat?.percentage || 0,
    };
  });

  // Sort pain points by score for list
  const sortedPainPoints = [...painPoints].sort((a, b) => b.score - a.score);

  const getSeverityColor = (score: number) => {
    if (score >= 70) return "text-red-600 bg-red-50 border-red-200";
    if (score >= 40) return "text-yellow-600 bg-yellow-50 border-yellow-200";
    return "text-green-600 bg-green-50 border-green-200";
  };

  const getSeverityLabel = (score: number) => {
    if (score >= 70) return "심각";
    if (score >= 40) return "주의";
    return "양호";
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-red-500" />
            <CardTitle>Pain Point Analysis</CardTitle>
          </div>
          <Badge variant="destructive">
            {painPoints.filter((p) => p.score >= 50).length}개 주요 문제
          </Badge>
        </div>
        <CardDescription>
          고객 불만 요소 및 구매 장벽 분석 (심각도 0-100)
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Radar Chart */}
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={radarData} margin={{ top: 20, right: 30, bottom: 20, left: 30 }}>
              <PolarGrid />
              <PolarAngleAxis
                dataKey="category"
                tick={{ fontSize: 12, fill: "#666" }}
              />
              <PolarRadiusAxis
                angle={90}
                domain={[0, 100]}
                tick={{ fontSize: 10 }}
                tickFormatter={(value) => `${value}`}
              />
              <Radar
                name="심각도"
                dataKey="severity"
                stroke="#ef4444"
                fill="#ef4444"
                fillOpacity={0.3}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <div className="bg-white p-3 border rounded-lg shadow-lg">
                        <p className="font-medium">{data.category}</p>
                        <p className="text-sm text-red-600">
                          심각도: {data.severity.toFixed(0)}점
                        </p>
                        <p className="text-sm text-muted-foreground">
                          언급 수: {data.count}건 ({data.percentage.toFixed(1)}%)
                        </p>
                        <p className="text-sm text-muted-foreground">
                          평균 SSR: {(data.avgSSR * 100).toFixed(1)}%
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Pain Point List */}
        <div className="mt-6 space-y-3">
          <h4 className="text-sm font-medium">주요 Pain Points</h4>
          {sortedPainPoints.length > 0 ? (
            <div className="space-y-2">
              {sortedPainPoints.slice(0, 5).map((point, index) => (
                <div
                  key={index}
                  className={`p-3 rounded-lg border ${getSeverityColor(point.score)}`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">
                        {CATEGORY_LABELS[point.category] || point.category}
                      </Badge>
                      <span className="text-xs font-medium">
                        {getSeverityLabel(point.score)}
                      </span>
                    </div>
                    <span className="font-bold">{point.score.toFixed(0)}점</span>
                  </div>
                  <p className="text-sm">{point.description}</p>
                  {point.affected_percentage > 0 && (
                    <p className="text-xs mt-1 opacity-70">
                      영향 받은 응답자: {point.affected_percentage.toFixed(1)}%
                    </p>
                  )}
                  {point.example_quotes.length > 0 && (
                    <p className="text-xs mt-2 italic border-t pt-2 opacity-70">
                      &quot;{point.example_quotes[0].slice(0, 80)}...&quot;
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-4">
              심각한 Pain Point가 발견되지 않았습니다.
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

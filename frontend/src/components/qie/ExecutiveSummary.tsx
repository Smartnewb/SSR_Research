"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Lightbulb, TrendingUp, TrendingDown, AlertTriangle } from "lucide-react";
import type { QIEAnalysis } from "@/lib/types";

interface ExecutiveSummaryProps {
  analysis: QIEAnalysis;
}

export function ExecutiveSummary({ analysis }: ExecutiveSummaryProps) {
  const { executive_summary, key_drivers, confidence_score } = analysis;

  const positiveDrivers = key_drivers.filter((d) => d.impact === "positive");
  const negativeDrivers = key_drivers.filter((d) => d.impact === "negative");

  const summaryLines = executive_summary
    .split("\n")
    .filter((line) => line.trim())
    .map((line) => line.replace(/^[-•*]\s*/, "").trim())
    .filter((line) => line.length > 0);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-yellow-500" />
            <CardTitle>Executive Summary</CardTitle>
          </div>
          <Badge
            variant={confidence_score >= 0.7 ? "default" : "secondary"}
            className={confidence_score >= 0.7 ? "bg-green-500" : ""}
          >
            신뢰도 {(confidence_score * 100).toFixed(0)}%
          </Badge>
        </div>
        <CardDescription>
          AI 심층 분석을 통해 도출된 핵심 인사이트
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Summary Points */}
        <div className="space-y-3">
          {summaryLines.length > 0 ? (
            summaryLines.slice(0, 5).map((line, index) => (
              <div
                key={index}
                className="flex items-start gap-3 p-3 bg-muted/50 rounded-lg"
              >
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary flex items-center justify-center text-sm font-medium">
                  {index + 1}
                </div>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {line}
                </p>
              </div>
            ))
          ) : (
            <p className="text-sm text-muted-foreground">{executive_summary}</p>
          )}
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="h-4 w-4 text-green-600" />
              <span className="text-sm font-medium text-green-800">
                긍정 요인
              </span>
            </div>
            <div className="text-2xl font-bold text-green-700">
              {positiveDrivers.length}개
            </div>
            {positiveDrivers.length > 0 && (
              <p className="text-xs text-green-600 mt-1">
                주요: {positiveDrivers[0]?.factor}
              </p>
            )}
          </div>

          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <TrendingDown className="h-4 w-4 text-red-600" />
              <span className="text-sm font-medium text-red-800">
                부정 요인
              </span>
            </div>
            <div className="text-2xl font-bold text-red-700">
              {negativeDrivers.length}개
            </div>
            {negativeDrivers.length > 0 && (
              <p className="text-xs text-red-600 mt-1">
                주요: {negativeDrivers[0]?.factor}
              </p>
            )}
          </div>
        </div>

        {/* Warning if low confidence */}
        {confidence_score < 0.6 && (
          <div className="flex items-center gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
            <p className="text-sm text-yellow-800">
              신뢰도가 낮습니다. 샘플 수를 늘리거나 추가 분석을 권장합니다.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

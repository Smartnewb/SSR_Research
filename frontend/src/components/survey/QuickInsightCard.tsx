"use client";

import { AlertTriangle, Lock, Sparkles, Zap } from "lucide-react";
import type { QuickInsight } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface QuickInsightCardProps {
  insight: QuickInsight;
  onUpgradeClick?: () => void;
}

const categoryColors: Record<string, string> = {
  Price: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  UX: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  Trust: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
  Feature: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  Convenience: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
  Other: "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200",
};

const categoryLabels: Record<string, string> = {
  Price: "가격",
  UX: "사용성",
  Trust: "신뢰도",
  Feature: "기능",
  Convenience: "편의성",
  Other: "기타",
};

export function QuickInsightCard({ insight, onUpgradeClick }: QuickInsightCardProps) {
  return (
    <Card className="border-2 border-dashed border-primary/30 bg-gradient-to-br from-primary/5 to-transparent">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Sparkles className="h-5 w-5 text-primary" />
          AI 인사이트 미리보기
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* One-liner insight */}
        <div className="rounded-lg bg-primary/10 p-4">
          <div className="flex items-start gap-2">
            <Zap className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
            <p className="text-sm font-medium leading-relaxed">
              {insight.one_liner}
            </p>
          </div>
        </div>

        {/* Pain Points */}
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-muted-foreground flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            발견된 주요 문제점 ({insight.pain_points.length}개)
          </h4>

          <div className="space-y-2">
            {insight.pain_points.map((point) => (
              <div
                key={point.rank}
                className={cn(
                  "rounded-lg border p-3 transition-all",
                  point.is_unlocked
                    ? "bg-card"
                    : "bg-muted/50 opacity-75"
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
                      {point.rank}
                    </span>
                    <span className="font-medium">{point.title}</span>
                    <Badge
                      variant="secondary"
                      className={cn("text-xs", categoryColors[point.category])}
                    >
                      {categoryLabels[point.category] || point.category}
                    </Badge>
                  </div>
                  {!point.is_unlocked && (
                    <Lock className="h-4 w-4 text-muted-foreground" />
                  )}
                </div>

                {point.is_unlocked && point.description ? (
                  <div className="mt-2 pl-8">
                    <p className="text-sm text-muted-foreground">
                      {point.description}
                    </p>
                    {point.affected_percentage !== undefined && (
                      <p className="mt-1 text-xs text-primary font-medium">
                        응답자의 {point.affected_percentage.toFixed(1)}%가 언급
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="mt-2 pl-8">
                    <p className="text-sm text-muted-foreground italic">
                      AI 심층 분석에서 확인하세요
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <Button
          onClick={onUpgradeClick}
          className="w-full"
          size="lg"
        >
          <Sparkles className="mr-2 h-4 w-4" />
          AI 심층 분석으로 해결책 확인하기
        </Button>
      </CardContent>
    </Card>
  );
}

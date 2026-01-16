"use client";

import { BarChart3, Clock, DollarSign, TrendingUp } from "lucide-react";
import type { SurveyResponse } from "@/lib/types";
import { formatCost, formatDuration, getScoreColor } from "@/lib/api";
import { MetricCard } from "./MetricCard";
import { ScoreDistribution } from "./ScoreDistribution";
import { ResponseTable } from "./ResponseTable";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

interface ResultsDashboardProps {
  results: SurveyResponse;
  onReset?: () => void;
}

export function ResultsDashboard({ results, onReset }: ResultsDashboardProps) {
  const exportToCSV = () => {
    const headers = ["persona_id", "ssr_score", "likert_5", "scale_10", "response_text"];
    const rows = results.results.map((r) => [
      r.persona_id,
      r.ssr_score.toFixed(4),
      r.likert_5.toFixed(2),
      r.scale_10.toFixed(2),
      `"${r.response_text.replace(/"/g, '""')}"`,
    ]);

    const csv = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `survey_${results.survey_id}.csv`;
    a.click();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Survey Results</h2>
          <p className="text-muted-foreground">ID: {results.survey_id}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={exportToCSV}>
            Export CSV
          </Button>
          {onReset && (
            <Button variant="outline" onClick={onReset}>
              New Survey
            </Button>
          )}
        </div>
      </div>

      <Card className="bg-muted/30">
        <CardContent className="pt-4">
          <p className="text-sm text-muted-foreground">Product:</p>
          <p className="font-medium">{results.product_description}</p>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="Average Score"
          value={`${(results.mean_score * 100).toFixed(1)}%`}
          subtitle={`Median: ${(results.median_score * 100).toFixed(1)}%`}
          colorClass={getScoreColor(results.mean_score)}
          icon={<TrendingUp className="h-8 w-8" />}
        />
        <MetricCard
          title="Std Deviation"
          value={`${(results.std_dev * 100).toFixed(1)}%`}
          subtitle={`Range: ${(results.min_score * 100).toFixed(0)}-${(results.max_score * 100).toFixed(0)}%`}
          icon={<BarChart3 className="h-8 w-8" />}
        />
        <MetricCard
          title="Total Cost"
          value={formatCost(results.total_cost)}
          subtitle={`${results.total_tokens} tokens`}
          icon={<DollarSign className="h-8 w-8" />}
        />
        <MetricCard
          title="Execution Time"
          value={formatDuration(results.execution_time_seconds)}
          subtitle={`${results.sample_size} respondents`}
          icon={<Clock className="h-8 w-8" />}
        />
      </div>

      <ScoreDistribution distribution={results.score_distribution} />

      <ResponseTable results={results.results} />
    </div>
  );
}

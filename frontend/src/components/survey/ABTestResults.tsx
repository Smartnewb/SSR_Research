"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ABTestResponse } from "@/lib/types";
import { formatCost, formatDuration, getScoreColor } from "@/lib/api";
import { MetricCard } from "./MetricCard";
import { Trophy, AlertTriangle, TrendingUp, Clock, DollarSign } from "lucide-react";

interface ABTestResultsProps {
  results: ABTestResponse;
  onReset?: () => void;
}

export function ABTestResults({ results, onReset }: ABTestResultsProps) {
  const { statistics, results_a, results_b } = results;

  const comparisonData = [
    {
      name: results.product_a_name,
      score: results_a.mean_score * 100,
      fill: "#3b82f6",
    },
    {
      name: results.product_b_name,
      score: results_b.mean_score * 100,
      fill: "#10b981",
    },
  ];

  const totalCost = results_a.total_cost + results_b.total_cost;
  const totalTime =
    results_a.execution_time_seconds + results_b.execution_time_seconds;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">A/B Test Results</h2>
          <p className="text-muted-foreground">ID: {results.test_id}</p>
        </div>
        {onReset && (
          <Button variant="outline" onClick={onReset}>
            New Test
          </Button>
        )}
      </div>

      {statistics.winner && (
        <Card
          className={
            statistics.significant ? "border-green-500 bg-green-50" : "border-yellow-500 bg-yellow-50"
          }
        >
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              {statistics.significant ? (
                <Trophy className="h-10 w-10 text-green-600" />
              ) : (
                <AlertTriangle className="h-10 w-10 text-yellow-600" />
              )}
              <div>
                <p className="text-lg font-semibold">
                  {statistics.significant
                    ? `Winner: ${statistics.winner}`
                    : "No Clear Winner"}
                </p>
                <p className="text-sm text-muted-foreground">
                  {statistics.significant
                    ? `Statistically significant (p = ${statistics.p_value.toFixed(4)})`
                    : `Not statistically significant (p = ${statistics.p_value.toFixed(4)})`}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              {results.product_a_name}
              {statistics.winner === results.product_a_name && (
                <Badge className="bg-green-500">Winner</Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <p className={`text-3xl font-bold ${getScoreColor(results_a.mean_score)}`}>
                {(results_a.mean_score * 100).toFixed(1)}%
              </p>
              <p className="text-sm text-muted-foreground">
                ± {(results_a.std_dev * 100).toFixed(1)}% std dev
              </p>
              <p className="text-sm text-muted-foreground">
                Range: {(results_a.min_score * 100).toFixed(0)}% -{" "}
                {(results_a.max_score * 100).toFixed(0)}%
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              {results.product_b_name}
              {statistics.winner === results.product_b_name && (
                <Badge className="bg-green-500">Winner</Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <p className={`text-3xl font-bold ${getScoreColor(results_b.mean_score)}`}>
                {(results_b.mean_score * 100).toFixed(1)}%
              </p>
              <p className="text-sm text-muted-foreground">
                ± {(results_b.std_dev * 100).toFixed(1)}% std dev
              </p>
              <p className="text-sm text-muted-foreground">
                Range: {(results_b.min_score * 100).toFixed(0)}% -{" "}
                {(results_b.max_score * 100).toFixed(0)}%
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Score Comparison</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={comparisonData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" domain={[0, 100]} unit="%" />
                <YAxis type="category" dataKey="name" width={100} />
                <Tooltip formatter={(value: number) => [`${value.toFixed(1)}%`, "Score"]} />
                <Bar dataKey="score" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Statistical Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Mean Difference</p>
              <p className="text-xl font-semibold">
                {(statistics.mean_difference * 100).toFixed(2)}%
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">p-value</p>
              <p className="text-xl font-semibold">{statistics.p_value.toFixed(4)}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Effect Size (Cohen's d)</p>
              <p className="text-xl font-semibold">{statistics.effect_size.toFixed(3)}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">95% CI</p>
              <p className="text-xl font-semibold">
                [{(statistics.confidence_interval[0] * 100).toFixed(1)}%,{" "}
                {(statistics.confidence_interval[1] * 100).toFixed(1)}%]
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-3 gap-4">
        <MetricCard
          title="Total Cost"
          value={formatCost(totalCost)}
          icon={<DollarSign className="h-6 w-6" />}
        />
        <MetricCard
          title="Total Time"
          value={formatDuration(totalTime)}
          icon={<Clock className="h-6 w-6" />}
        />
        <MetricCard
          title="Total Respondents"
          value={results_a.sample_size + results_b.sample_size}
          icon={<TrendingUp className="h-6 w-6" />}
        />
      </div>
    </div>
  );
}

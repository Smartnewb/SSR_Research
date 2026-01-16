"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Download, Home, Trophy, BarChart3, FlaskConical, Users } from "lucide-react";
import { toast } from "sonner";

interface ConceptScore {
  concept_id: string;
  concept_title: string;
  mean_score: number;
  median_score: number;
  std_dev: number;
  score_distribution: Record<string, number>;
  results: Array<{
    persona_id: string;
    concept_id: string;
    demographics: {
      age: number;
      gender: string;
      income: string;
      location: string;
    };
    response_text: string;
    ssr_score: number;
  }>;
}

interface ComparisonStatistics {
  test_type: "none" | "t_test" | "anova";
  statistic: number | null;
  p_value: number | null;
  is_significant: boolean;
  winner: string | null;
  interpretation: string;
}

interface ExecutionResult {
  job_id: string;
  workflow_id: string;
  total_respondents: number;
  execution_time: number;
  mean_score: number;
  median_score: number;
  std_dev: number;
  score_distribution: Record<string, number>;
  results: Array<{
    persona_id: string;
    concept_id?: string;
    demographics: {
      age: number;
      gender: string;
      income: string;
      location: string;
    };
    response_text: string;
    ssr_score: number;
  }>;
  comparison_mode: "single" | "ab_test" | "multi_compare";
  concept_scores: ConceptScore[] | null;
  comparison_stats: ComparisonStatistics | null;
}

export default function ResultsPage() {
  const params = useParams();
  const router = useRouter();
  const workflowId = params.id as string;

  const [results, setResults] = useState<ExecutionResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const response = await fetch(
          `http://localhost:8000/api/workflows/${workflowId}/execute/result`
        );

        if (!response.ok) {
          throw new Error("Failed to fetch results");
        }

        const data = await response.json();
        setResults(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, [workflowId]);

  const handleExportJSON = () => {
    if (!results) return;
    const dataStr = JSON.stringify(results, null, 2);
    const blob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `survey_results_${workflowId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success("JSON 파일 다운로드 완료!");
  };

  const handleExportCSV = () => {
    if (!results) return;

    const headers = ["persona_id", "concept_id", "age", "gender", "income", "location", "ssr_score", "response_text"];
    const rows = results.results.map((r) => [
      r.persona_id,
      r.concept_id || "",
      r.demographics.age,
      r.demographics.gender,
      r.demographics.income,
      r.demographics.location,
      r.ssr_score.toFixed(4),
      `"${r.response_text.replace(/"/g, '""')}"`,
    ]);

    const csv = [headers.join(","), ...rows.map((row) => row.join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `survey_results_${workflowId}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success("CSV 파일 다운로드 완료!");
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto py-8 text-center">
        <div className="animate-pulse">결과를 불러오는 중...</div>
      </div>
    );
  }

  if (error || !results) {
    return (
      <div className="max-w-6xl mx-auto py-8">
        <div className="bg-destructive/10 border border-destructive text-destructive p-4 rounded">
          {error || "결과를 찾을 수 없습니다"}
        </div>
      </div>
    );
  }

  const getComparisonModeInfo = () => {
    switch (results.comparison_mode) {
      case "single":
        return { label: "단일 설문", color: "bg-blue-500", icon: BarChart3 };
      case "ab_test":
        return { label: "A/B 테스팅", color: "bg-purple-500", icon: FlaskConical };
      case "multi_compare":
        return { label: "Multi-Compare", color: "bg-orange-500", icon: Trophy };
      default:
        return { label: "설문 결과", color: "bg-gray-500", icon: BarChart3 };
    }
  };

  const modeInfo = getComparisonModeInfo();
  const ModeIcon = modeInfo.icon;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <ModeIcon className="h-6 w-6" />
            설문 결과
          </h1>
          <p className="text-muted-foreground mt-1">
            Job ID: {results.job_id}
          </p>
        </div>
        <Badge className={`${modeInfo.color} text-white`}>{modeInfo.label}</Badge>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              총 응답 수
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold flex items-center gap-2">
              <Users className="h-6 w-6 text-muted-foreground" />
              {results.total_respondents}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              평균 SSR 점수
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {(results.mean_score * 100).toFixed(1)}%
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              중앙값
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {(results.median_score * 100).toFixed(1)}%
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              실행 시간
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {results.execution_time.toFixed(1)}초
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Comparison Results - Only for A/B or Multi-Compare */}
      {results.comparison_mode !== "single" && results.concept_scores && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Trophy className="h-5 w-5" />
              컨셉별 점수 비교
            </CardTitle>
            <CardDescription>
              {results.comparison_mode === "ab_test"
                ? "두 컨셉의 SSR 점수를 비교합니다"
                : "여러 컨셉의 SSR 점수를 비교합니다"}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {results.concept_scores
              .sort((a, b) => b.mean_score - a.mean_score)
              .map((concept, idx) => (
                <div key={concept.concept_id} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Badge
                        variant={idx === 0 ? "default" : "outline"}
                        className={idx === 0 ? "bg-yellow-500" : ""}
                      >
                        #{idx + 1}
                      </Badge>
                      <span className="font-medium">{concept.concept_title}</span>
                      {idx === 0 && results.comparison_stats?.is_significant && (
                        <Badge variant="outline" className="text-green-600 border-green-600">
                          승자
                        </Badge>
                      )}
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold">
                        {(concept.mean_score * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs text-muted-foreground">
                        ±{(concept.std_dev * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                  <Progress
                    value={concept.mean_score * 100}
                    className="h-3"
                  />
                </div>
              ))}
          </CardContent>
        </Card>
      )}

      {/* Statistical Significance */}
      {results.comparison_stats && results.comparison_stats.test_type !== "none" && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FlaskConical className="h-5 w-5" />
              통계적 유의성 분석
            </CardTitle>
            <CardDescription>
              테스트: {results.comparison_stats.test_type === "t_test" ? "독립 표본 t-검정" : "일원분산분석 (ANOVA)"}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-4 bg-muted/50 rounded-lg">
                <div className="text-sm text-muted-foreground mb-1">통계량</div>
                <div className="text-xl font-bold">
                  {results.comparison_stats.statistic?.toFixed(3) || "N/A"}
                </div>
              </div>
              <div className="text-center p-4 bg-muted/50 rounded-lg">
                <div className="text-sm text-muted-foreground mb-1">p-value</div>
                <div className="text-xl font-bold">
                  {results.comparison_stats.p_value?.toFixed(4) || "N/A"}
                </div>
              </div>
              <div className="text-center p-4 bg-muted/50 rounded-lg">
                <div className="text-sm text-muted-foreground mb-1">유의수준</div>
                <div className="text-xl font-bold">
                  α = 0.05
                </div>
              </div>
            </div>

            <Separator />

            <div className="flex items-start gap-3">
              <Badge
                variant={results.comparison_stats.is_significant ? "default" : "secondary"}
                className={results.comparison_stats.is_significant ? "bg-green-500" : ""}
              >
                {results.comparison_stats.is_significant ? "유의미함" : "유의미하지 않음"}
              </Badge>
              <p className="text-sm text-muted-foreground">
                {results.comparison_stats.interpretation}
              </p>
            </div>

            {results.comparison_stats.winner && (
              <div className="flex items-center gap-2 p-4 bg-green-50 border border-green-200 rounded-lg">
                <Trophy className="h-5 w-5 text-green-600" />
                <span className="font-medium text-green-800">
                  승자: {results.comparison_stats.winner}
                </span>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Score Distribution - Single Concept */}
      {results.comparison_mode === "single" && (
        <Card>
          <CardHeader>
            <CardTitle>SSR 점수 분포</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(results.score_distribution)
                .sort(([a], [b]) => parseFloat(b) - parseFloat(a))
                .map(([score, count]) => {
                  const percentage = ((count as number) / results.total_respondents) * 100;
                  return (
                    <div key={score} className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span>점수 {score}</span>
                        <span>
                          {count}명 ({percentage.toFixed(1)}%)
                        </span>
                      </div>
                      <div className="w-full bg-muted rounded-full h-2">
                        <div
                          className="bg-primary h-2 rounded-full"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Sample Responses */}
      <Card>
        <CardHeader>
          <CardTitle>샘플 응답</CardTitle>
          <CardDescription>
            상위 10개 응답을 표시합니다
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {results.results.slice(0, 10).map((result, index) => (
              <div
                key={index}
                className="border rounded-lg p-4 space-y-2 bg-muted/30"
              >
                <div className="flex justify-between items-start">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold">
                        {result.persona_id}
                      </span>
                      {result.concept_id && (
                        <Badge variant="outline" className="text-xs">
                          {result.concept_id}
                        </Badge>
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {result.demographics.age}세 • {result.demographics.gender} •{" "}
                      {result.demographics.income} • {result.demographics.location}
                    </div>
                  </div>
                  <div className="text-lg font-bold">
                    {(result.ssr_score * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="text-sm text-muted-foreground">
                  {result.response_text}
                </div>
              </div>
            ))}
          </div>

          {results.results.length > 10 && (
            <div className="text-center text-sm text-muted-foreground mt-4">
              {results.results.length}개 응답 중 10개 표시 중
            </div>
          )}
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <Button variant="outline" className="flex-1" onClick={handleExportCSV}>
          <Download className="mr-2 h-4 w-4" />
          CSV 다운로드
        </Button>
        <Button variant="outline" className="flex-1" onClick={handleExportJSON}>
          <Download className="mr-2 h-4 w-4" />
          JSON 다운로드
        </Button>
        <Button className="flex-1" onClick={() => router.push("/")}>
          <Home className="mr-2 h-4 w-4" />
          새 설문 시작
        </Button>
      </div>
    </div>
  );
}

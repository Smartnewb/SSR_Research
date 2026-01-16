"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Download, Play, Users, BarChart3, ArrowLeft } from "lucide-react";
import { toast } from "sonner";

interface GenerationResult {
  job_id: string;
  workflow_id: string;
  total_personas: number;
  distribution_stats: {
    age: { mean: number; std: number; min: number; max: number };
    gender: Record<string, number>;
    income: Record<string, number>;
  };
  personas: Array<{
    id: string;
    age: number;
    gender: string;
    income_bracket: string;
    income_value: number;
    location: string;
    category_usage: string;
    shopping_behavior: string;
    pain_points: string[];
    decision_drivers: string[];
  }>;
}

export default function GeneratingPersonasPage() {
  const params = useParams();
  const router = useRouter();
  const workflowId = params.id as string;

  const [status, setStatus] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [generationResult, setGenerationResult] = useState<GenerationResult | null>(null);
  const [isLoadingResult, setIsLoadingResult] = useState(false);

  useEffect(() => {
    const startGeneration = async () => {
      try {
        const response = await fetch(
          `http://localhost:8000/api/workflows/${workflowId}/generate/start`,
          {
            method: "POST",
          }
        );

        if (!response.ok) {
          throw new Error("Failed to start generation");
        }

        pollStatus();
      } catch (err: any) {
        setError(err.message);
      }
    };

    const pollStatus = () => {
      const interval = setInterval(async () => {
        try {
          const response = await fetch(
            `http://localhost:8000/api/workflows/${workflowId}/generate/status`
          );

          if (!response.ok) {
            throw new Error("Failed to get status");
          }

          const data = await response.json();
          setStatus(data);

          if (data.status === "completed") {
            clearInterval(interval);
            fetchGenerationResult();
          }

          if (data.status === "failed") {
            clearInterval(interval);
            setError(data.error || "Generation failed");
          }
        } catch (err: any) {
          console.error("Error polling status:", err);
        }
      }, 500);

      return () => clearInterval(interval);
    };

    startGeneration();
  }, [workflowId]);

  const fetchGenerationResult = async () => {
    setIsLoadingResult(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/workflows/${workflowId}/generate/result`
      );
      if (response.ok) {
        const result = await response.json();
        setGenerationResult(result);
      }
    } catch (err) {
      console.error("Error fetching generation result:", err);
    } finally {
      setIsLoadingResult(false);
    }
  };

  const handleDownloadJSON = () => {
    if (!generationResult) return;

    const exportData = {
      export_version: "1.0",
      exported_at: new Date().toISOString(),
      workflow_id: workflowId,
      generation: generationResult,
    };

    const dataStr = JSON.stringify(exportData, null, 2);
    const blob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `personas_${workflowId}_${generationResult.total_personas}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success(`${generationResult.total_personas}개 페르소나 JSON 다운로드 완료!`);
  };

  const handleStartSurvey = () => {
    router.push(`/workflows/${workflowId}/concepts`);
  };

  const incomeLabels: Record<string, string> = {
    none: "무소득/학생",
    low: "저소득",
    mid: "중소득",
    high: "고소득",
  };

  const genderLabels: Record<string, string> = {
    female: "여성",
    male: "남성",
  };

  if (generationResult) {
    const stats = generationResult.distribution_stats;
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push(`/workflows/${workflowId}/persona`)}
          className="mb-2"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          페르소나 수정 (다시 생성)
        </Button>

        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Step 5: 페르소나 생성 완료</h1>
          <div className="text-sm text-muted-foreground">7단계 중 5단계</div>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <Users className="h-5 w-5 text-green-600" />
            <span className="text-green-800 font-semibold">
              {generationResult.total_personas}개 페르소나 생성 완료!
            </span>
          </div>
          <p className="text-sm text-green-700 mt-1">
            아래에서 생성된 페르소나의 분포를 확인하고, JSON 파일로 다운로드할 수 있습니다.
          </p>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                나이 분포
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats.age.mean.toFixed(1)}세
              </div>
              <p className="text-xs text-muted-foreground">
                평균 (범위: {stats.age.min}~{stats.age.max}세)
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                성별 분포
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-1">
                {Object.entries(stats.gender).map(([gender, count]) => (
                  <div key={gender} className="flex justify-between text-sm">
                    <span>{genderLabels[gender] || gender}</span>
                    <span className="font-semibold">
                      {((count / generationResult.total_personas) * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                소득 분포
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-1">
                {Object.entries(stats.income).map(([bracket, count]) => (
                  <div key={bracket} className="flex justify-between text-sm">
                    <span>{incomeLabels[bracket] || bracket}</span>
                    <span className="font-semibold">
                      {((count / generationResult.total_personas) * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              샘플 페르소나 (처음 5명)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-2">ID</th>
                    <th className="text-left py-2 px-2">나이</th>
                    <th className="text-left py-2 px-2">성별</th>
                    <th className="text-left py-2 px-2">소득</th>
                    <th className="text-left py-2 px-2">쇼핑 성향</th>
                  </tr>
                </thead>
                <tbody>
                  {generationResult.personas.slice(0, 5).map((persona) => (
                    <tr key={persona.id} className="border-b">
                      <td className="py-2 px-2 font-mono text-xs">{persona.id}</td>
                      <td className="py-2 px-2">{persona.age}세</td>
                      <td className="py-2 px-2">{genderLabels[persona.gender] || persona.gender}</td>
                      <td className="py-2 px-2">{incomeLabels[persona.income_bracket] || persona.income_bracket}</td>
                      <td className="py-2 px-2">{persona.shopping_behavior}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        <div className="flex gap-4">
          <Button
            onClick={handleDownloadJSON}
            variant="outline"
            className="flex-1"
            size="lg"
          >
            <Download className="mr-2 h-4 w-4" />
            JSON 다운로드 ({generationResult.total_personas}명)
          </Button>
          <Button
            onClick={handleStartSurvey}
            className="flex-1"
            size="lg"
          >
            <Play className="mr-2 h-4 w-4" />
            다음: 컨셉 설정
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Step 5: 페르소나 생성 중</h1>
        <div className="text-sm text-muted-foreground">7단계 중 5단계</div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>페르소나 변형 생성 중...</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {error ? (
            <div className="bg-destructive/10 border border-destructive text-destructive p-4 rounded">
              {error}
            </div>
          ) : status ? (
            <>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>
                    상태: <span className="font-semibold capitalize">{status.status}</span>
                  </span>
                  <span>
                    {status.generated_count} / {status.total_personas}
                  </span>
                </div>
                <Progress value={status.progress * 100} />
              </div>

              <div className="bg-muted/50 p-4 rounded-lg space-y-2">
                <h4 className="font-semibold text-sm">진행 상황</h4>
                <p className="text-sm text-muted-foreground">
                  코어 페르소나를 기반으로 {status.total_personas}개의 고유한 페르소나 변형을 생성하고 있습니다.
                  각 페르소나는 전체 분포를 유지하면서 약간씩 다른 인구통계학적 특성을 가집니다.
                </p>
              </div>

              {status.status === "completed" && isLoadingResult && (
                <div className="text-center space-y-2">
                  <div className="text-green-600 font-semibold">
                    ✓ 생성 완료!
                  </div>
                  <p className="text-sm text-muted-foreground">
                    결과를 불러오는 중...
                  </p>
                </div>
              )}
            </>
          ) : (
            <div className="text-center text-muted-foreground">
              생성을 시작하는 중...
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

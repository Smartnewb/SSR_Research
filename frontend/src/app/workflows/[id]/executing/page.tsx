"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, FlaskConical } from "lucide-react";

interface ExecutionStatus {
  job_id: string;
  workflow_id: string;
  status: string;
  total_respondents: number;
  completed_count: number;
  progress: number;
  error?: string;
}

interface Workflow {
  id: string;
  status: string;
  concepts?: Array<{ id: string; title: string }>;
}

export default function ExecutingSurveyPage() {
  const params = useParams();
  const router = useRouter();
  const workflowId = params.id as string;

  const [status, setStatus] = useState<ExecutionStatus | null>(null);
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [error, setError] = useState<string | null>(null);

  // interval 참조를 저장하여 cleanup 시 정리
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  // 실행 시작 여부를 추적하여 중복 실행 방지
  const hasStartedRef = useRef(false);
  // 연속 에러 횟수 추적
  const consecutiveErrorsRef = useRef(0);
  const MAX_CONSECUTIVE_ERRORS = 5;
  // 현재 폴링 간격 (지수 백오프용)
  const currentIntervalRef = useRef(500);
  const BASE_INTERVAL = 500;
  const MAX_INTERVAL = 10000;
  // 재시도 가능 여부
  const [canRetry, setCanRetry] = useState(false);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearTimeout(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const scheduleNextPoll = useCallback(() => {
    const poll = async () => {
      try {
        const response = await fetch(
          `http://localhost:8000/api/workflows/${workflowId}/execute/status`
        );

        if (!response.ok) {
          // 404는 리소스가 존재하지 않음 - 즉시 중단
          if (response.status === 404) {
            stopPolling();
            setCanRetry(true);
            const errorData = await response.json().catch(() => ({}));
            setError(errorData.detail || "실행 정보를 찾을 수 없습니다. 설문이 아직 시작되지 않았거나 만료되었습니다.");
            return;
          }
          throw new Error("Failed to get status");
        }

        // 성공 시 에러 카운트 리셋 및 간격 초기화
        consecutiveErrorsRef.current = 0;
        currentIntervalRef.current = BASE_INTERVAL;
        const data = await response.json();
        setStatus(data);

        if (data.status === "completed") {
          stopPolling();
          setTimeout(() => {
            router.push(`/workflows/${workflowId}/results`);
          }, 1000);
          return;
        }

        if (data.status === "failed") {
          stopPolling();
          setCanRetry(true);
          setError(data.error || "Execution failed");
          return;
        }

        // 다음 폴링 예약
        intervalRef.current = setTimeout(scheduleNextPoll, currentIntervalRef.current);
      } catch (err: any) {
        consecutiveErrorsRef.current += 1;
        console.error(`Polling error (${consecutiveErrorsRef.current}/${MAX_CONSECUTIVE_ERRORS}):`, err.message);

        // 연속 에러가 임계값 초과 시 폴링 중단
        if (consecutiveErrorsRef.current >= MAX_CONSECUTIVE_ERRORS) {
          stopPolling();
          setCanRetry(true);
          setError(`서버 연결에 실패했습니다 (${MAX_CONSECUTIVE_ERRORS}회 재시도 후 중단). 백엔드 서버가 실행 중인지 확인해주세요.`);
          return;
        }

        // 지수 백오프: 간격을 2배로 늘림 (최대 10초)
        currentIntervalRef.current = Math.min(currentIntervalRef.current * 2, MAX_INTERVAL);
        console.log(`Next retry in ${currentIntervalRef.current}ms`);
        intervalRef.current = setTimeout(scheduleNextPoll, currentIntervalRef.current);
      }
    };

    poll();
  }, [workflowId, router, stopPolling]);

  const startPolling = useCallback(() => {
    // 이미 폴링 중이면 중복 시작 방지
    if (intervalRef.current) return;
    // 폴링 시작 시 초기화
    consecutiveErrorsRef.current = 0;
    currentIntervalRef.current = BASE_INTERVAL;
    setCanRetry(false);
    setError(null);

    scheduleNextPoll();
  }, [scheduleNextPoll]);

  useEffect(() => {
    // 이미 시작했으면 중복 실행 방지
    if (hasStartedRef.current) return;
    hasStartedRef.current = true;

    const fetchWorkflowAndStart = async () => {
      try {
        const workflowRes = await fetch(
          `http://localhost:8000/api/workflows/${workflowId}`
        );
        if (!workflowRes.ok) {
          throw new Error("Workflow not found");
        }

        const workflowData = await workflowRes.json();
        setWorkflow(workflowData);

        // 이미 완료된 워크플로우면 결과 페이지로 리다이렉트
        if (workflowData.status === "completed") {
          router.push(`/workflows/${workflowId}/results`);
          return;
        }

        // 이미 설문이 실행 중이면 start_execution 호출하지 않고 pollStatus만 실행
        if (workflowData.status === "surveying" && workflowData.survey_execution_job_id) {
          startPolling();
          return;
        }

        const response = await fetch(
          `http://localhost:8000/api/workflows/${workflowId}/execute/start?use_mock=false`,
          {
            method: "POST",
          }
        );

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || "Failed to start execution");
        }

        startPolling();
      } catch (err: any) {
        setError(err.message);
      }
    };

    fetchWorkflowAndStart();

    // Cleanup: 컴포넌트 언마운트 시 polling 중지
    return () => {
      stopPolling();
    };
  }, [workflowId, router, startPolling, stopPolling]);

  const getComparisonMode = () => {
    const conceptCount = workflow?.concepts?.length || 1;
    if (conceptCount === 1) return { label: "단일 설문", color: "bg-blue-500" };
    if (conceptCount === 2) return { label: "A/B 테스팅", color: "bg-purple-500" };
    return { label: `Multi-Compare`, color: "bg-orange-500" };
  };

  const mode = getComparisonMode();
  const conceptCount = workflow?.concepts?.length || 1;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => router.push(`/workflows/${workflowId}/concepts`)}
        className="mb-2"
        disabled={status?.status === "executing"}
      >
        <ArrowLeft className="h-4 w-4 mr-2" />
        컨셉 관리
      </Button>

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Step 7: 설문 실행 중</h1>
        <div className="text-sm text-muted-foreground">7단계 중 7단계</div>
      </div>

      <div className="bg-blue-50 border border-blue-300 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <span className="text-blue-600 text-xl">🔬</span>
          <div>
            <p className="font-semibold text-blue-900">SSR 논문 방식으로 실제 설문 실행 중</p>
            <p className="text-sm text-blue-800 mt-1">
              GPT를 사용하여 각 페르소나의 <strong>자유 텍스트 응답</strong>을 수집하고,
              임베딩 기반 <strong>Semantic Similarity Rating</strong>으로 구매 의향을 측정합니다.
            </p>
            <p className="text-xs text-blue-700 mt-2">
              API 비용이 발생합니다. 100명 기준 약 $0.5~1 예상.
            </p>
          </div>
        </div>
      </div>

      {workflow?.concepts && workflow.concepts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <FlaskConical className="h-5 w-5" />
              테스트 정보
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4 mb-4">
              <Badge className={`${mode.color} text-white`}>{mode.label}</Badge>
              <span className="text-sm text-muted-foreground">
                {conceptCount}개 컨셉 테스트 중
              </span>
            </div>
            <div className="flex flex-wrap gap-2">
              {workflow.concepts.map((concept, idx) => (
                <Badge key={concept.id} variant="outline">
                  {idx + 1}. {concept.title || concept.id}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>설문 진행 상황</CardTitle>
          <CardDescription>
            {conceptCount > 1
              ? `${conceptCount}개 컨셉에 대해 각 페르소나의 반응을 수집하고 있습니다`
              : "각 페르소나가 제품에 대한 의견을 제공하고 있습니다"}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {error ? (
            <div className="bg-destructive/10 border border-destructive text-destructive p-4 rounded">
              <p className="font-semibold mb-1">오류 발생</p>
              <p className="text-sm">{error}</p>
              <div className="flex gap-2 mt-3">
                {canRetry && (
                  <Button
                    variant="default"
                    size="sm"
                    onClick={() => startPolling()}
                  >
                    다시 시도
                  </Button>
                )}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => router.push(`/workflows/${workflowId}/concepts`)}
                >
                  컨셉 관리로 돌아가기
                </Button>
              </div>
            </div>
          ) : status ? (
            <>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>
                    상태: <span className="font-semibold capitalize">{status.status}</span>
                  </span>
                  <span>
                    {status.completed_count} / {status.total_respondents} 응답
                  </span>
                </div>
                <Progress value={status.progress * 100} className="h-3" />
                <div className="text-right text-xs text-muted-foreground">
                  {(status.progress * 100).toFixed(1)}%
                </div>
              </div>

              <div className="bg-muted/50 p-4 rounded-lg space-y-2">
                <h4 className="font-semibold text-sm">현재 진행 중인 작업</h4>
                <p className="text-sm text-muted-foreground">
                  {conceptCount === 1 && (
                    "각 페르소나가 제품 설명을 검토하고 의견을 제공합니다. SSR(의미적 유사도 평점) 점수로 구매 의향을 측정합니다."
                  )}
                  {conceptCount === 2 && (
                    "각 페르소나가 두 컨셉을 비교 평가합니다. t-test를 통해 통계적으로 유의미한 차이가 있는지 분석합니다."
                  )}
                  {conceptCount >= 3 && (
                    `${conceptCount}개 컨셉에 대한 평가를 수집하고 있습니다. ANOVA 분석을 통해 컨셉 간 유의미한 차이를 파악합니다.`
                  )}
                </p>
              </div>

              {status.status === "completed" && (
                <div className="text-center space-y-2 py-4">
                  <div className="text-green-600 font-semibold text-lg">
                    ✓ 설문 완료!
                  </div>
                  <p className="text-sm text-muted-foreground">
                    결과 페이지로 이동합니다...
                  </p>
                </div>
              )}
            </>
          ) : (
            <div className="text-center text-muted-foreground py-8">
              <div className="animate-pulse">설문을 시작하는 중...</div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

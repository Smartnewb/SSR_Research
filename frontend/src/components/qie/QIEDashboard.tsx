"use client";

import { useEffect, useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Loader2, Brain, RefreshCw, Clock, Zap, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { ExecutiveSummary } from "./ExecutiveSummary";
import { KeyDriversChart } from "./KeyDriversChart";
import { PainPointRadar } from "./PainPointRadar";
import { ActionItemsList } from "./ActionItemsList";
import type { QIEResultResponse, QIEJobResponse, QIEJobStatus } from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_BASE_URL = API_BASE_URL.replace(/^http/, "ws");

interface QIEDashboardProps {
  workflowId: string;
}

const STAGE_LABELS: Record<string, string> = {
  pending: "대기 중",
  tier1_processing: "응답 태깅 중",
  aggregating: "통계 집계 중",
  tier2_synthesis: "심층 분석 중",
  completed: "완료",
  failed: "실패",
};

export function QIEDashboard({ workflowId }: QIEDashboardProps) {
  const [result, setResult] = useState<QIEResultResponse | null>(null);
  const [jobStatus, setJobStatus] = useState<QIEJobResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchResult = useCallback(async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/workflows/${workflowId}/qie/result`
      );
      if (response.ok) {
        const data = await response.json();
        setResult(data);
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }, [workflowId]);

  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/workflows/${workflowId}/qie/status`
      );
      if (response.ok) {
        const data = await response.json();
        setJobStatus(data);
        return data;
      }
      return null;
    } catch {
      return null;
    }
  }, [workflowId]);

  const checkExistingAnalysis = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    // Try to get existing result first
    const hasResult = await fetchResult();
    if (hasResult) {
      setIsLoading(false);
      return;
    }

    // Check if there's a running job
    const status = await fetchStatus();
    if (status && !["completed", "failed"].includes(status.status)) {
      // Job is running, start polling
      pollForCompletion();
    }

    setIsLoading(false);
  }, [fetchResult, fetchStatus]);

  const pollForCompletion = useCallback(async () => {
    const interval = setInterval(async () => {
      const status = await fetchStatus();
      if (!status) {
        clearInterval(interval);
        return;
      }

      if (status.status === "completed") {
        clearInterval(interval);
        await fetchResult();
        toast.success("AI 심층 분석이 완료되었습니다!");
      } else if (status.status === "failed") {
        clearInterval(interval);
        setError(status.error || "분석 중 오류가 발생했습니다.");
        toast.error("분석 실패: " + (status.error || "알 수 없는 오류"));
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [fetchStatus, fetchResult]);

  useEffect(() => {
    checkExistingAnalysis();
  }, [checkExistingAnalysis]);

  // WebSocket for real-time progress with reconnection
  useEffect(() => {
    if (!jobStatus || ["completed", "failed"].includes(jobStatus.status)) {
      return;
    }

    let ws: WebSocket | null = null;
    let reconnectAttempts = 0;
    let reconnectTimeout: NodeJS.Timeout | null = null;
    let isCleaningUp = false;
    const maxReconnectAttempts = 5;
    const baseDelay = 1000;

    const connect = () => {
      if (isCleaningUp) return;

      ws = new WebSocket(
        `${WS_BASE_URL}/ws/workflows/${workflowId}/progress`
      );

      ws.onopen = () => {
        reconnectAttempts = 0;
      };

      ws.onmessage = async (event) => {
        const message = JSON.parse(event.data);
        if (message.type === "qie_progress") {
          setJobStatus((prev) =>
            prev
              ? {
                  ...prev,
                  progress: message.progress,
                  status: message.status as QIEJobStatus,
                  current_stage: message.stage,
                  message: message.message,
                  processed_count: message.processed,
                }
              : null
          );

          if (message.status === "completed") {
            await fetchResult();
            toast.success("AI 심층 분석이 완료되었습니다!");
          }
        }
      };

      ws.onclose = (event) => {
        if (isCleaningUp || event.code === 1000) return;

        if (reconnectAttempts < maxReconnectAttempts) {
          const delay = baseDelay * Math.pow(2, reconnectAttempts);
          reconnectAttempts++;
          reconnectTimeout = setTimeout(connect, delay);
        }
      };

      ws.onerror = () => {
        ws?.close();
      };
    };

    connect();

    return () => {
      isCleaningUp = true;
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      ws?.close(1000, "Component unmounting");
    };
  }, [workflowId, jobStatus?.status, fetchResult]);

  const startAnalysis = async (force: boolean = false) => {
    setIsStarting(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/workflows/${workflowId}/qie/start?force=${force}`,
        { method: "POST" }
      );

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "분석 시작 실패");
      }

      const data = await response.json();
      setJobStatus(data);
      setResult(null);
      toast.success("AI 심층 분석을 시작합니다...");

      // Start polling
      pollForCompletion();
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "알 수 없는 오류";
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsStarting(false);
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // Analysis in progress
  if (jobStatus && !["completed", "failed"].includes(jobStatus.status) && !result) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5 animate-pulse text-purple-500" />
            AI 심층 분석 진행 중
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span>{STAGE_LABELS[jobStatus.current_stage] || jobStatus.current_stage}</span>
              <span>{(jobStatus.progress * 100).toFixed(0)}%</span>
            </div>
            <Progress value={jobStatus.progress * 100} className="h-3" />
          </div>

          <p className="text-sm text-muted-foreground text-center">
            {jobStatus.message || "분석 중..."}
          </p>

          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="p-3 bg-muted/50 rounded-lg">
              <div className="text-2xl font-bold">{jobStatus.total_responses}</div>
              <div className="text-xs text-muted-foreground">총 응답</div>
            </div>
            <div className="p-3 bg-muted/50 rounded-lg">
              <div className="text-2xl font-bold">{jobStatus.processed_count}</div>
              <div className="text-xs text-muted-foreground">처리 완료</div>
            </div>
            <div className="p-3 bg-muted/50 rounded-lg">
              <Badge variant="secondary" className="text-xs">
                {STAGE_LABELS[jobStatus.status] || jobStatus.status}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="pt-6">
          <div className="flex items-center gap-3 text-red-600">
            <AlertCircle className="h-5 w-5" />
            <p>{error}</p>
          </div>
          <Button
            onClick={() => startAnalysis(true)}
            className="mt-4"
            variant="outline"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            다시 시도
          </Button>
        </CardContent>
      </Card>
    );
  }

  // No analysis yet
  if (!result) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center space-y-4">
            <Brain className="h-12 w-12 mx-auto text-purple-500" />
            <div>
              <h3 className="font-medium">AI 심층 분석</h3>
              <p className="text-sm text-muted-foreground mt-1">
                GPT-5.2 기반의 Two-Tier Map-Reduce 분석을 통해
                <br />
                구매 의도의 &quot;왜(Why)&quot;를 파악합니다.
              </p>
            </div>
            <div className="flex gap-4 justify-center text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />약 20초 소요
              </span>
              <span className="flex items-center gap-1">
                <Zap className="h-3 w-3" />비용 $0.30 이하
              </span>
            </div>
            <Button
              onClick={() => startAnalysis(false)}
              disabled={isStarting}
              className="bg-purple-600 hover:bg-purple-700"
            >
              {isStarting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  시작 중...
                </>
              ) : (
                <>
                  <Brain className="h-4 w-4 mr-2" />
                  AI 심층 분석 시작
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Display results
  return (
    <div className="space-y-6">
      {/* Header with timing info */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="h-5 w-5 text-purple-500" />
          <h2 className="text-lg font-semibold">AI 심층 분석 결과</h2>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-xs text-muted-foreground">
            <span>총 {result.execution_time.toFixed(1)}초</span>
            <span className="mx-2">|</span>
            <span>Tier1: {result.tier1_time.toFixed(1)}초</span>
            <span className="mx-2">|</span>
            <span>Tier2: {result.tier2_time.toFixed(1)}초</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => startAnalysis(true)}
            disabled={isStarting}
          >
            <RefreshCw className={`h-4 w-4 mr-1 ${isStarting ? "animate-spin" : ""}`} />
            재분석
          </Button>
        </div>
      </div>

      {/* Executive Summary */}
      <ExecutiveSummary analysis={result.analysis} />

      {/* Charts Grid */}
      <div className="grid md:grid-cols-2 gap-6">
        <KeyDriversChart keyDrivers={result.analysis.key_drivers} />
        <PainPointRadar
          painPoints={result.analysis.pain_points}
          aggregatedStats={result.aggregated_stats}
        />
      </div>

      {/* Action Items */}
      <ActionItemsList actionItems={result.analysis.action_items} />
    </div>
  );
}

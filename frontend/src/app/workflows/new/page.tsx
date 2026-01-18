"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Workflow {
  id: string;
  status: string;
  current_step: number;
  product?: {
    name: string;
    category: string;
    description: string;
  };
  core_persona?: any;
  sample_size?: number;
  concepts?: any[];
  created_at?: string;
  updated_at?: string;
}

function formatDateTime(dateString?: string): string {
  if (!dateString) return "";
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  const timeStr = date.toLocaleTimeString("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });

  if (diffDays === 0) {
    return `오늘 ${timeStr}`;
  } else if (diffDays === 1) {
    return `어제 ${timeStr}`;
  } else if (diffDays < 7) {
    return `${diffDays}일 전`;
  } else {
    return date.toLocaleDateString("ko-KR", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  }
}

export default function NewWorkflowPage() {
  const router = useRouter();
  const [creating, setCreating] = useState(false);
  const [previousWorkflows, setPreviousWorkflows] = useState<Workflow[]>([]);
  const [loadingWorkflows, setLoadingWorkflows] = useState(true);
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null);
  const [deletingWorkflow, setDeletingWorkflow] = useState<string | null>(null);

  useEffect(() => {
    loadPreviousWorkflows();
  }, []);

  const handleDeleteWorkflow = async (e: React.MouseEvent, workflowId: string) => {
    e.stopPropagation();
    if (!confirm("이 설문 데이터를 삭제하시겠습니까?")) return;

    setDeletingWorkflow(workflowId);
    try {
      const response = await fetch(`http://localhost:8000/api/workflows/${workflowId}`, {
        method: "DELETE",
      });
      if (response.ok) {
        setPreviousWorkflows((prev) => prev.filter((w) => w.id !== workflowId));
        if (selectedWorkflow === workflowId) {
          setSelectedWorkflow(null);
        }
      }
    } catch (error) {
      console.error("Error deleting workflow:", error);
    } finally {
      setDeletingWorkflow(null);
    }
  };

  const loadPreviousWorkflows = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/workflows");
      if (response.ok) {
        const workflows = await response.json();
        // Only show workflows that have product data
        const completedWorkflows = workflows.filter((w: Workflow) => w.product);
        setPreviousWorkflows(completedWorkflows.slice(0, 5)); // Show last 5
      }
    } catch (error) {
      console.error("Error loading workflows:", error);
    } finally {
      setLoadingWorkflows(false);
    }
  };

  const getStepRoute = (step: number): string => {
    const stepRoutes: Record<number, string> = {
      1: "product",
      2: "persona",
      3: "confirm",
      4: "sample-size",
      5: "generating",
      6: "concepts",
      7: "executing",
    };
    return stepRoutes[step] || "product";
  };

  const handleCreateWorkflow = async (copyFrom?: string) => {
    setCreating(true);
    try {
      const url = copyFrom
        ? `http://localhost:8000/api/workflows?copy_from=${copyFrom}`
        : "http://localhost:8000/api/workflows";

      const response = await fetch(url, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("Failed to create workflow");
      }

      const data = await response.json();
      const route = getStepRoute(data.current_step);
      router.push(`/workflows/${data.workflow_id}/${route}`);
    } catch (error) {
      console.error("Error creating workflow:", error);
      alert("Failed to create workflow");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold">새 설문조사 시작</h1>

      {!loadingWorkflows && previousWorkflows.length > 0 && (
        <Card className="border-2 border-blue-200 bg-blue-50/30">
          <CardHeader>
            <CardTitle>💾 이전 설정 불러오기</CardTitle>
            <p className="text-sm text-muted-foreground pt-2">
              이전에 작성했던 제품 정보와 페르소나를 재사용할 수 있습니다.
            </p>
          </CardHeader>
          <CardContent className="space-y-3">
            {previousWorkflows.map((workflow) => {
              const savedData = [];
              if (workflow.product) savedData.push("제품");
              if (workflow.core_persona) savedData.push("페르소나");
              if (workflow.sample_size) savedData.push(`샘플 ${workflow.sample_size}명`);
              if (workflow.concepts?.length) savedData.push(`컨셉 ${workflow.concepts.length}개`);

              return (
                <div
                  key={workflow.id}
                  role="button"
                  tabIndex={0}
                  className={`relative w-full p-4 rounded-lg border-2 cursor-pointer transition-all text-left ${
                    selectedWorkflow === workflow.id
                      ? "border-blue-500 bg-blue-100"
                      : "border-gray-200 bg-white hover:border-blue-300"
                  }`}
                  onClick={() => setSelectedWorkflow(workflow.id)}
                  onKeyDown={(e) => e.key === "Enter" && setSelectedWorkflow(workflow.id)}
                >
                  <button
                    type="button"
                    onClick={(e) => handleDeleteWorkflow(e, workflow.id)}
                    disabled={deletingWorkflow === workflow.id}
                    className="absolute top-2 right-2 p-1 rounded-full hover:bg-red-100 text-gray-400 hover:text-red-500 transition-colors"
                    title="삭제"
                  >
                    {deletingWorkflow === workflow.id ? (
                      <span className="text-xs">...</span>
                    ) : (
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                    )}
                  </button>
                  <div className="flex items-start justify-between pr-6">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold">
                          {workflow.product?.name || "제품명 없음"}
                        </span>
                        {workflow.updated_at && (
                          <span className="text-xs text-muted-foreground bg-gray-100 px-2 py-0.5 rounded">
                            {formatDateTime(workflow.updated_at)}
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {workflow.product?.category || "카테고리 없음"}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1 line-clamp-1">
                        {workflow.product?.description || ""}
                      </div>
                      <div className="flex flex-wrap gap-1 mt-2">
                        {savedData.map((item) => (
                          <span
                            key={item}
                            className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800"
                          >
                            ✓ {item}
                          </span>
                        ))}
                      </div>
                    </div>
                    {selectedWorkflow === workflow.id && (
                      <div className="text-blue-600 text-sm font-semibold ml-4">
                        선택됨 ✓
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            <Button
              onClick={() =>
                selectedWorkflow
                  ? handleCreateWorkflow(selectedWorkflow)
                  : null
              }
              disabled={!selectedWorkflow || creating}
              className="w-full"
              size="lg"
            >
              {creating ? "생성 중..." : "선택한 설정으로 시작하기"}
            </Button>

            <div className="text-center">
              <Button
                variant="link"
                onClick={() => setSelectedWorkflow(null)}
                className="text-xs"
              >
                또는 처음부터 새로 시작
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>🆕 새로 시작하기</CardTitle>
          <p className="text-sm text-muted-foreground pt-2">
            제품 정보부터 처음부터 입력하여 시작합니다.
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-4">
            <h3 className="font-semibold text-lg">7단계 워크플로우</h3>
            <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
              <li>제품 설명 작성</li>
              <li>핵심 페르소나 구체화 (7개 필수 항목)</li>
              <li>페르소나 확인</li>
              <li>샘플 사이즈 선택</li>
              <li>페르소나 variations 생성</li>
              <li>설문 실행</li>
              <li>결과 확인</li>
            </ol>
          </div>

          <div className="bg-muted/50 p-4 rounded-lg space-y-2">
            <h4 className="font-semibold text-sm">💡 Tip: Gemini 시장조사</h4>
            <p className="text-sm text-muted-foreground">
              2단계에서 Gemini Deep Research를 활용하여 실제 시장 데이터로
              페르소나를 검증하고 개선할 수 있습니다.
            </p>
          </div>

          <Button
            onClick={() => handleCreateWorkflow()}
            disabled={creating}
            size="lg"
            className="w-full"
            variant="outline"
          >
            {creating ? "생성 중..." : "처음부터 시작하기"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

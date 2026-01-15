"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Workflow {
  id: string;
  status: string;
  product?: {
    name: string;
    category: string;
    description: string;
  };
  persona?: any;
}

export default function NewWorkflowPage() {
  const router = useRouter();
  const [creating, setCreating] = useState(false);
  const [previousWorkflows, setPreviousWorkflows] = useState<Workflow[]>([]);
  const [loadingWorkflows, setLoadingWorkflows] = useState(true);
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null);

  useEffect(() => {
    loadPreviousWorkflows();
  }, []);

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
      router.push(`/workflows/${data.workflow_id}/product`);
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
            {previousWorkflows.map((workflow) => (
              <button
                key={workflow.id}
                type="button"
                className={`w-full p-4 rounded-lg border-2 cursor-pointer transition-all text-left ${
                  selectedWorkflow === workflow.id
                    ? "border-blue-500 bg-blue-100"
                    : "border-gray-200 bg-white hover:border-blue-300"
                }`}
                onClick={() => setSelectedWorkflow(workflow.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="font-semibold">
                      {workflow.product?.name || "제품명 없음"}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {workflow.product?.category || "카테고리 없음"}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1 line-clamp-1">
                      {workflow.product?.description || ""}
                    </div>
                  </div>
                  {selectedWorkflow === workflow.id && (
                    <div className="text-blue-600 text-sm font-semibold ml-4">
                      선택됨 ✓
                    </div>
                  )}
                </div>
              </button>
            ))}

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

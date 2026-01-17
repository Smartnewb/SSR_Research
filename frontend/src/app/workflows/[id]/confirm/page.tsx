"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft } from "lucide-react";

interface Archetype {
  segment_id: string;
  segment_name: string;
  share_ratio: number;
  demographics: {
    age_range: [number, number];
    gender_distribution: { female: number; male: number };
  };
  income_level: string;
  category_usage: string;
  shopping_behavior: string;
  core_traits: string[];
  pain_points: string[];
  decision_drivers: string[];
}

export default function ConfirmPersonaPage() {
  const params = useParams();
  const router = useRouter();
  const workflowId = params.id as string;

  const [workflow, setWorkflow] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    const fetchWorkflow = async () => {
      try {
        const response = await fetch(
          `http://localhost:8000/api/workflows/${workflowId}`
        );
        const data = await response.json();
        setWorkflow(data);
      } catch (error) {
        console.error("Error fetching workflow:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchWorkflow();
  }, [workflowId]);

  const handleConfirm = async () => {
    setConfirming(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/workflows/${workflowId}/confirm`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        throw new Error("Failed to confirm persona");
      }

      router.push(`/workflows/${workflowId}/sample-size`);
    } catch (error) {
      console.error("Error confirming persona:", error);
      alert("Failed to confirm persona");
    } finally {
      setConfirming(false);
    }
  };

  const handleEdit = () => {
    router.push(`/workflows/${workflowId}/persona`);
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  // Check for multi-archetype mode or single persona mode
  const isMultiArchetypeMode = workflow?.use_multi_archetype && workflow?.archetypes?.length > 0;
  const hasSinglePersona = workflow?.core_persona;

  if (!workflow || (!isMultiArchetypeMode && !hasSinglePersona)) {
    return <div>Persona not found</div>;
  }

  const persona = workflow.core_persona;
  const archetypes: Archetype[] = workflow.archetypes || [];

  // Helper function to get income level label
  const getIncomeLevelLabel = (level: string) => {
    const labels: Record<string, string> = {
      none: "무소득/학생",
      low: "저소득",
      mid: "중소득",
      high: "고소득",
    };
    return labels[level] || level;
  };

  // Helper function to get category usage label
  const getCategoryUsageLabel = (usage: string) => {
    const labels: Record<string, string> = {
      high: "높음 (매일 사용)",
      medium: "보통 (주 1~2회)",
      low: "낮음 (가끔 사용)",
    };
    return labels[usage] || usage;
  };

  // Helper function to get shopping behavior label
  const getShoppingBehaviorLabel = (behavior: string) => {
    const labels: Record<string, string> = {
      smart_shopper: "신중형",
      quality: "품질 중시형",
      budget: "가격 중시형",
      impulsive: "충동 구매형",
      price_sensitive: "가격 민감형",
    };
    return labels[behavior] || behavior;
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => router.push(`/workflows/${workflowId}/persona`)}
        className="mb-2"
      >
        <ArrowLeft className="h-4 w-4 mr-2" />
        페르소나 수정
      </Button>

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Step 3: 타겟 고객 확인</h1>
        <div className="text-sm text-muted-foreground">7단계 중 3단계</div>
      </div>

      {isMultiArchetypeMode ? (
        /* Multi-Archetype Mode UI */
        <Card>
          <CardHeader>
            <CardTitle>선택된 타겟 고객 그룹 ({archetypes.length}개)</CardTitle>
            <p className="text-sm text-muted-foreground pt-1">
              아래 그룹들의 비율에 따라 페르소나가 생성됩니다.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            {archetypes.map((arch, index) => (
              <div
                key={arch.segment_id || index}
                className="p-4 border rounded-lg bg-muted/30"
              >
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-lg">{arch.segment_name}</h3>
                  <span className="px-3 py-1 text-sm font-medium bg-purple-100 text-purple-800 rounded-full">
                    점유율 {Math.round(arch.share_ratio * 100)}%
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
                  <div>
                    <span className="font-medium text-muted-foreground">연령대:</span>{" "}
                    {arch.demographics?.age_range?.[0]}~{arch.demographics?.age_range?.[1]}세
                  </div>
                  <div>
                    <span className="font-medium text-muted-foreground">성별:</span>{" "}
                    여 {arch.demographics?.gender_distribution?.female}% / 남{" "}
                    {arch.demographics?.gender_distribution?.male}%
                  </div>
                  <div>
                    <span className="font-medium text-muted-foreground">소득 수준:</span>{" "}
                    {getIncomeLevelLabel(arch.income_level)}
                  </div>
                  <div>
                    <span className="font-medium text-muted-foreground">사용 빈도:</span>{" "}
                    {getCategoryUsageLabel(arch.category_usage)}
                  </div>
                  <div>
                    <span className="font-medium text-muted-foreground">쇼핑 성향:</span>{" "}
                    {getShoppingBehaviorLabel(arch.shopping_behavior)}
                  </div>
                </div>

                {arch.core_traits && arch.core_traits.length > 0 && (
                  <div className="mt-3">
                    <span className="text-sm font-medium text-muted-foreground">핵심 특성:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {arch.core_traits.map((trait, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded"
                        >
                          {trait}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {arch.pain_points && arch.pain_points.length > 0 && (
                  <div className="mt-2">
                    <span className="text-sm font-medium text-muted-foreground">주요 고민:</span>
                    <ul className="text-sm text-muted-foreground list-disc list-inside mt-1">
                      {arch.pain_points.slice(0, 3).map((point, i) => (
                        <li key={i}>{point}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}

            <div className="flex gap-2 pt-4">
              <Button onClick={handleEdit} variant="outline" className="flex-1">
                그룹 다시 선택
              </Button>
              <Button
                onClick={handleConfirm}
                disabled={confirming}
                className="flex-1"
              >
                {confirming ? "확인 중..." : "확인하고 다음 단계로 →"}
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        /* Single Persona Mode UI (legacy) */
        <Card>
          <CardHeader>
            <CardTitle>Review Your Core Persona</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <div className="text-sm font-semibold">Age Range</div>
                <div className="text-sm text-muted-foreground">
                  {persona.age_range[0]} - {persona.age_range[1]} years
                </div>
              </div>

              <div className="space-y-1">
                <div className="text-sm font-semibold">Location</div>
                <div className="text-sm text-muted-foreground capitalize">
                  {persona.location}
                </div>
              </div>
            </div>

            <div className="space-y-1">
              <div className="text-sm font-semibold">Gender Distribution</div>
              <div className="text-sm text-muted-foreground">
                {Object.entries(persona.gender_distribution)
                  .map(([k, v]) => {
                    const val = v as number;
                    const percent = val <= 1 ? Math.round(val * 100) : val;
                    return `${k}: ${percent}%`;
                  })
                  .join(", ")}
              </div>
            </div>

            <div className="space-y-1">
              <div className="text-sm font-semibold">Income Brackets</div>
              <div className="text-sm text-muted-foreground">
                {Object.entries(persona.income_brackets)
                  .map(([k, v]) => {
                    const val = v as number;
                    const percent = val <= 1 ? Math.round(val * 100) : val;
                    return `${k}: ${percent}%`;
                  })
                  .join(", ")}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <div className="text-sm font-semibold">Category Usage</div>
                <div className="text-sm text-muted-foreground capitalize">
                  {persona.category_usage}
                </div>
              </div>

              <div className="space-y-1">
                <div className="text-sm font-semibold">Shopping Behavior</div>
                <div className="text-sm text-muted-foreground capitalize">
                  {persona.shopping_behavior.replace("_", " ")}
                </div>
              </div>
            </div>

            <div className="space-y-1">
              <div className="text-sm font-semibold">Key Pain Points</div>
              <ul className="text-sm text-muted-foreground list-disc list-inside">
                {persona.key_pain_points.map((point: string) => (
                  <li key={point}>{point}</li>
                ))}
              </ul>
            </div>

            <div className="space-y-1">
              <div className="text-sm font-semibold">Decision Drivers</div>
              <ul className="text-sm text-muted-foreground list-disc list-inside">
                {persona.decision_drivers.map((driver: string) => (
                  <li key={driver}>{driver}</li>
                ))}
              </ul>
            </div>

            <div className="flex gap-2 pt-4">
              <Button onClick={handleEdit} variant="outline" className="flex-1">
                Edit Persona
              </Button>
              <Button
                onClick={handleConfirm}
                disabled={confirming}
                className="flex-1"
              >
                {confirming ? "Confirming..." : "Confirm & Continue"}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

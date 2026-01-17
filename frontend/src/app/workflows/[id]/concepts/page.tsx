"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Plus, Trash2, Play, ArrowLeft, Package, FlaskConical } from "lucide-react";
import type { ConceptInput } from "@/lib/types";

interface Workflow {
  id: string;
  status: string;
  current_step: number;
  product?: {
    name: string;
    category: string;
    description: string;
    features: string[];
    price_point: string;
    target_market: string;
  };
  concepts?: ConceptInput[];
}

const emptyConceptTemplate = (id: string): ConceptInput => ({
  id,
  title: "",
  headline: "",
  consumer_insight: "",
  benefits: [""],
  rtb: [""],
  image_prompt: "",
  price: "",
});

export default function ConceptsManagementPage() {
  const params = useParams();
  const router = useRouter();
  const workflowId = params.id as string;

  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [concepts, setConcepts] = useState<ConceptInput[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchWorkflow = async () => {
      try {
        const response = await fetch(
          `http://localhost:8000/api/workflows/${workflowId}`
        );
        if (!response.ok) {
          throw new Error("Failed to fetch workflow");
        }
        const data = await response.json();
        setWorkflow(data);

        if (data.concepts && data.concepts.length > 0) {
          setConcepts(data.concepts);
        } else {
          await createConceptFromProduct();
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchWorkflow();
  }, [workflowId]);

  const createConceptFromProduct = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/workflows/${workflowId}/concepts/from-product`,
        { method: "POST" }
      );
      if (response.ok) {
        const data = await response.json();
        setWorkflow(data);
        setConcepts(data.concepts || []);
      } else {
        // API 실패 시 빈 컨셉으로 시작
        console.warn("Failed to create concept from product, using empty template");
        setConcepts([emptyConceptTemplate("CONCEPT_001")]);
      }
    } catch (err) {
      console.error("Error creating concept from product:", err);
      // 네트워크 오류 시에도 빈 컨셉으로 시작할 수 있도록 함
      setConcepts([emptyConceptTemplate("CONCEPT_001")]);
    }
  };

  const addConcept = () => {
    if (concepts.length >= 5) {
      toast.error("최대 5개의 컨셉까지 추가할 수 있습니다");
      return;
    }
    const newId = `CONCEPT_${String(concepts.length + 1).padStart(3, "0")}`;
    setConcepts([...concepts, emptyConceptTemplate(newId)]);
  };

  const removeConcept = (index: number) => {
    if (concepts.length <= 1) {
      toast.error("최소 1개의 컨셉이 필요합니다");
      return;
    }
    setConcepts(concepts.filter((_, i) => i !== index));
  };

  const updateConcept = (index: number, field: keyof ConceptInput, value: string) => {
    const updated = [...concepts];
    updated[index] = { ...updated[index], [field]: value };
    setConcepts(updated);
  };

  const validateConcepts = () => {
    for (const concept of concepts) {
      if (!concept.title || !concept.headline || !concept.price) {
        toast.error("모든 컨셉의 필수 필드(제목, 헤드라인, 가격)를 입력해주세요");
        return false;
      }
      if (!concept.benefits || concept.benefits.filter(b => b.trim()).length === 0) {
        toast.error("최소 1개의 혜택을 입력해주세요");
        return false;
      }
    }
    return true;
  };

  const updateListField = (
    conceptIndex: number,
    field: "benefits" | "rtb",
    itemIndex: number,
    value: string
  ) => {
    const updated = [...concepts];
    const list = [...(updated[conceptIndex][field] || [])];
    list[itemIndex] = value;
    updated[conceptIndex] = { ...updated[conceptIndex], [field]: list };
    setConcepts(updated);
  };

  const addListItem = (conceptIndex: number, field: "benefits" | "rtb") => {
    const updated = [...concepts];
    const list = [...(updated[conceptIndex][field] || [])];
    if (list.length >= 5) {
      toast.error("최대 5개까지 추가할 수 있습니다");
      return;
    }
    list.push("");
    updated[conceptIndex] = { ...updated[conceptIndex], [field]: list };
    setConcepts(updated);
  };

  const removeListItem = (conceptIndex: number, field: "benefits" | "rtb", itemIndex: number) => {
    const updated = [...concepts];
    const list = [...(updated[conceptIndex][field] || [])];
    if (list.length <= 1) {
      toast.error("최소 1개는 필요합니다");
      return;
    }
    list.splice(itemIndex, 1);
    updated[conceptIndex] = { ...updated[conceptIndex], [field]: list };
    setConcepts(updated);
  };

  const saveConcepts = async () => {
    if (!validateConcepts()) return;

    setIsSaving(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/workflows/${workflowId}/concepts`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ concepts }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to save concepts");
      }

      const data = await response.json();
      setWorkflow(data);
      toast.success("컨셉이 저장되었습니다");
      return true;
    } catch (err: any) {
      toast.error(err.message || "컨셉 저장 실패");
      return false;
    } finally {
      setIsSaving(false);
    }
  };

  const handleStartSurvey = async () => {
    const saved = await saveConcepts();
    if (saved) {
      router.push(`/workflows/${workflowId}/executing`);
    }
  };

  const getComparisonMode = () => {
    if (concepts.length === 1) return { label: "단일 설문", color: "bg-blue-500" };
    if (concepts.length === 2) return { label: "A/B 테스팅", color: "bg-purple-500" };
    return { label: `Multi-Compare (${concepts.length}개)`, color: "bg-orange-500" };
  };

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto py-8 text-center">
        <div className="animate-pulse">데이터를 불러오는 중...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto py-8">
        <div className="bg-destructive/10 border border-destructive text-destructive p-4 rounded">
          {error}
        </div>
      </div>
    );
  }

  const mode = getComparisonMode();

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => router.push(`/workflows/${workflowId}/generating`)}
        className="mb-2"
      >
        <ArrowLeft className="h-4 w-4 mr-2" />
        페르소나 확인
      </Button>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Step 6: 컨셉 관리</h1>
          <p className="text-muted-foreground mt-1">
            설문에 사용할 제품 컨셉을 관리합니다
          </p>
        </div>
        <div className="text-sm text-muted-foreground">7단계 중 6단계</div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <FlaskConical className="h-5 w-5" />
            테스트 모드
          </CardTitle>
          <CardDescription>
            컨셉 수에 따라 자동으로 테스트 모드가 결정됩니다
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <Badge className={`${mode.color} text-white`}>{mode.label}</Badge>
            <span className="text-sm text-muted-foreground">
              {concepts.length === 1 && "단일 제품에 대한 SSR 점수를 측정합니다"}
              {concepts.length === 2 && "두 컨셉을 t-test로 통계적 비교합니다"}
              {concepts.length >= 3 && "여러 컨셉을 ANOVA로 통계적 비교합니다"}
            </span>
          </div>
        </CardContent>
      </Card>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Package className="h-5 w-5" />
            컨셉 목록 ({concepts.length}/5)
          </h2>
          <Button onClick={addConcept} disabled={concepts.length >= 5} size="sm">
            <Plus className="mr-2 h-4 w-4" />
            컨셉 추가
          </Button>
        </div>

        {concepts.map((concept, index) => (
          <Card key={concept.id} className={index === 0 ? "border-primary" : ""}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CardTitle className="text-lg">
                    컨셉 {index + 1}
                    {index === 0 && (
                      <Badge variant="outline" className="ml-2">
                        기본 (제품 기반)
                      </Badge>
                    )}
                  </CardTitle>
                </div>
                <Button
                  onClick={() => removeConcept(index)}
                  disabled={concepts.length <= 1}
                  variant="ghost"
                  size="sm"
                >
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>
                    제목 <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    value={concept.title}
                    onChange={(e) => updateConcept(index, "title", e.target.value)}
                    placeholder="예: 콜게이트 3일 화이트닝"
                  />
                </div>
                <div className="space-y-2">
                  <Label>
                    가격 <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    value={concept.price}
                    onChange={(e) => updateConcept(index, "price", e.target.value)}
                    placeholder="예: 8,900원 (120g)"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>
                  헤드라인 <span className="text-destructive">*</span>
                </Label>
                <Input
                  value={concept.headline}
                  onChange={(e) => updateConcept(index, "headline", e.target.value)}
                  placeholder="예: 단 3일, 2단계 더 밝은 미소"
                />
              </div>

              <div className="space-y-2">
                <Label>소비자 인사이트</Label>
                <Textarea
                  value={concept.consumer_insight}
                  onChange={(e) => updateConcept(index, "consumer_insight", e.target.value)}
                  placeholder="예: 커피로 누렇게 변한 치아 때문에 웃기가 꺼려지시나요?"
                  rows={2}
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>
                    핵심 혜택 <span className="text-destructive">*</span>
                  </Label>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => addListItem(index, "benefits")}
                    disabled={(concept.benefits?.length || 0) >= 5}
                  >
                    <Plus className="h-3 w-3 mr-1" />
                    추가
                  </Button>
                </div>
                <div className="space-y-2">
                  {(concept.benefits || [""]).map((benefit, bIndex) => (
                    <div key={bIndex} className="flex gap-2">
                      <Input
                        value={benefit}
                        onChange={(e) => updateListField(index, "benefits", bIndex, e.target.value)}
                        placeholder={`혜택 ${bIndex + 1}: 예) 집에서 편하게 전문가급 미백 효과를`}
                      />
                      {(concept.benefits?.length || 0) > 1 && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeListItem(index, "benefits", bIndex)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>신뢰 근거 (RTB)</Label>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => addListItem(index, "rtb")}
                    disabled={(concept.rtb?.length || 0) >= 5}
                  >
                    <Plus className="h-3 w-3 mr-1" />
                    추가
                  </Button>
                </div>
                <div className="space-y-2">
                  {(concept.rtb || [""]).map((rtbItem, rIndex) => (
                    <div key={rIndex} className="flex gap-2">
                      <Input
                        value={rtbItem}
                        onChange={(e) => updateListField(index, "rtb", rIndex, e.target.value)}
                        placeholder={`RTB ${rIndex + 1}: 예) 특허 받은 과산화수소 3% 포뮬러`}
                      />
                      {(concept.rtb?.length || 0) > 1 && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeListItem(index, "rtb", rIndex)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <Label>이미지 프롬프트</Label>
                <Textarea
                  value={concept.image_prompt}
                  onChange={(e) => updateConcept(index, "image_prompt", e.target.value)}
                  placeholder="예: A sleek red toothpaste tube on marble counter, soft morning light, minimalist style, high-end product photography"
                  rows={3}
                />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="flex gap-4 pt-4">
        <Button
          onClick={saveConcepts}
          variant="outline"
          className="flex-1"
          size="lg"
          disabled={isSaving}
        >
          {isSaving ? "저장 중..." : "컨셉 저장"}
        </Button>
        <Button
          onClick={handleStartSurvey}
          className="flex-1"
          size="lg"
          disabled={isSaving}
        >
          <Play className="mr-2 h-4 w-4" />
          설문 시작 ({mode.label})
        </Button>
      </div>
    </div>
  );
}

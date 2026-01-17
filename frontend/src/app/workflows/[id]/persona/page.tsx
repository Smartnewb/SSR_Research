"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { ArrowLeft } from "lucide-react";

export default function CorePersonaPage() {
  const params = useParams();
  const router = useRouter();
  const workflowId = params.id as string;

  const [formData, setFormData] = useState({
    age_range: [25, 45] as [number, number],
    gender_distribution: { female: 50, male: 50 },
    income_brackets: { none: 10, low: 25, mid: 45, high: 20 },
    location: "urban",
    category_usage: "medium",
    shopping_behavior: "smart_shopper",
    key_pain_points: [] as string[],
    decision_drivers: [] as string[],
    currency: "KRW" as "KRW" | "USD",
  });

  const [painPointInput, setPainPointInput] = useState("");
  const [driverInput, setDriverInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [dataLoaded, setDataLoaded] = useState(false);

  const [researchPrompt, setResearchPrompt] = useState("");
  const [researchReport, setResearchReport] = useState("");
  const [parsingReport, setParsingReport] = useState(false);
  const [parsingProgress, setParsingProgress] = useState(0);
  const [generatingPrompt, setGeneratingPrompt] = useState(false);

  // Multi-Archetype states
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
  const [archetypes, setArchetypes] = useState<Archetype[]>([]);
  const [selectedArchetypeIds, setSelectedArchetypeIds] = useState<string[]>([]);
  const [showArchetypeSelection, setShowArchetypeSelection] = useState(false);
  const [savingArchetypes, setSavingArchetypes] = useState(false);

  useEffect(() => {
    loadWorkflowData();
  }, [workflowId]);

  const loadWorkflowData = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/workflows/${workflowId}`
      );
      if (response.ok) {
        const workflow = await response.json();
        // Check both persona and core_persona fields (core_persona is used after confirm step)
        const personaData = workflow.core_persona || workflow.persona;
        if (personaData) {
          // Convert 0-1 float values to 0-100 percentage if needed
          const convertToPercentage = (dist: Record<string, number>) => {
            const values = Object.values(dist);
            const isFloat = values.every(v => v >= 0 && v <= 1);
            if (isFloat && values.reduce((a, b) => a + b, 0) <= 1.1) {
              return Object.fromEntries(
                Object.entries(dist).map(([k, v]) => [k, Math.round(v * 100)])
              );
            }
            return dist;
          };

          // Ensure income_brackets has all 4 keys after conversion
          const rawIncomeBrackets = convertToPercentage(
            personaData.income_brackets || { none: 0.1, low: 0.25, mid: 0.45, high: 0.2 }
          );
          const incomeBracketsWithNone = {
            none: rawIncomeBrackets.none ?? 0,
            low: rawIncomeBrackets.low ?? 0,
            mid: rawIncomeBrackets.mid ?? 0,
            high: rawIncomeBrackets.high ?? 0,
          };

          const rawGender = convertToPercentage(
            personaData.gender_distribution || { female: 0.5, male: 0.5 }
          );
          const genderWithDefaults = {
            female: rawGender.female ?? 50,
            male: rawGender.male ?? 50,
          };

          setFormData({
            age_range: personaData.age_range || [25, 45],
            gender_distribution: genderWithDefaults,
            income_brackets: incomeBracketsWithNone,
            location: personaData.location || "urban",
            category_usage: personaData.category_usage || "medium",
            shopping_behavior:
              personaData.shopping_behavior || "smart_shopper",
            key_pain_points: personaData.key_pain_points || [],
            decision_drivers: personaData.decision_drivers || [],
            currency: personaData.currency || "KRW",
          });
          setDataLoaded(true);
        }
      }
    } catch (error) {
      console.error("Error loading workflow data:", error);
    }
  };

  const handleNumberInputFocus = (e: React.FocusEvent<HTMLInputElement>) => {
    e.target.select();
  };

  const handleAddPainPoint = () => {
    if (painPointInput.trim()) {
      setFormData({
        ...formData,
        key_pain_points: [...formData.key_pain_points, painPointInput.trim()],
      });
      setPainPointInput("");
    }
  };

  const handleRemovePainPoint = (index: number) => {
    setFormData({
      ...formData,
      key_pain_points: formData.key_pain_points.filter((_, i) => i !== index),
    });
  };

  const handleAddDriver = () => {
    if (driverInput.trim()) {
      setFormData({
        ...formData,
        decision_drivers: [...formData.decision_drivers, driverInput.trim()],
      });
      setDriverInput("");
    }
  };

  const handleRemoveDriver = (index: number) => {
    setFormData({
      ...formData,
      decision_drivers: formData.decision_drivers.filter((_, i) => i !== index),
    });
  };

  const handleGenerateResearchPrompt = async () => {
    setGeneratingPrompt(true);
    try {
      const workflowResponse = await fetch(
        `http://localhost:8000/api/workflows/${workflowId}`
      );
      const workflow = await workflowResponse.json();

      if (!workflow.product) {
        alert("제품 설명을 먼저 입력해주세요");
        setGeneratingPrompt(false);
        return;
      }

      // Check if user has filled any persona fields
      const hasPersonaData =
        formData.key_pain_points.length > 0 ||
        formData.decision_drivers.length > 0 ||
        formData.age_range[0] !== 25 ||
        formData.age_range[1] !== 45 ||
        formData.gender_distribution.female !== 50 ||
        formData.income_brackets.low !== 30;

      // Build request - persona draft is optional
      const requestBody: any = {
        product_category: workflow.product.category,
        product_description: workflow.product.description,
        product_name: workflow.product.name || "",
        target_market: workflow.product.target_market || "",
        price_point: workflow.product.price_point || "",
      };

      // Only include persona draft if user has entered some data
      if (hasPersonaData) {
        requestBody.initial_persona_draft = {
          age_range: formData.age_range,
          gender_distribution: {
            female: formData.gender_distribution.female / 100,
            male: formData.gender_distribution.male / 100,
          },
          income_brackets: {
            none: (formData.income_brackets.none ?? 0) / 100,
            low: (formData.income_brackets.low ?? 0) / 100,
            mid: (formData.income_brackets.mid ?? 0) / 100,
            high: (formData.income_brackets.high ?? 0) / 100,
          },
          location: formData.location,
          category_usage: formData.category_usage,
          shopping_behavior: formData.shopping_behavior,
          key_pain_points: formData.key_pain_points,
          decision_drivers: formData.decision_drivers,
        };
      }

      const response = await fetch(
        "http://localhost:8000/api/research/generate-prompt?use_mock=false",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(requestBody),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error("API Error:", errorData);
        throw new Error("Failed to generate research prompt");
      }

      const data = await response.json();
      setResearchPrompt(data.research_prompt);
    } catch (error) {
      console.error("Error generating research prompt:", error);
      alert("연구 프롬프트 생성에 실패했습니다.");
    } finally {
      setGeneratingPrompt(false);
    }
  };

  const handleParseResearchReport = async () => {
    if (!researchReport.trim()) {
      alert("리서치 보고서를 붙여넣어 주세요");
      return;
    }

    setParsingReport(true);
    setParsingProgress(10);
    try {
      // Get workflow for product context
      const workflowResponse = await fetch(
        `http://localhost:8000/api/workflows/${workflowId}`
      );
      const workflow = await workflowResponse.json();
      const productCategory = workflow.product?.category || "";

      setParsingProgress(30);

      // Call /api/archetypes/segment to get 3-5 target groups
      const response = await fetch(
        "http://localhost:8000/api/archetypes/segment",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            research_report: researchReport,
            product_category: productCategory,
            target_segments: 4,
          }),
        }
      );

      setParsingProgress(70);

      if (!response.ok) {
        throw new Error("Failed to segment market from research report");
      }

      const data = await response.json();
      setParsingProgress(90);

      // Store archetypes and show selection UI
      setArchetypes(data.archetypes || []);
      setSelectedArchetypeIds([]);
      setShowArchetypeSelection(true);
      setParsingProgress(100);

      if (data.warnings && data.warnings.length > 0) {
        console.warn("Segmentation warnings:", data.warnings);
      }
    } catch (error) {
      console.error("Error parsing report:", error);
      alert("리서치 보고서 분석에 실패했습니다. 다시 시도해주세요.");
    } finally {
      setParsingReport(false);
      setParsingProgress(0);
    }
  };

  // Save selected archetypes to backend and navigate to confirm page
  const handleApplyArchetypes = async () => {
    if (selectedArchetypeIds.length === 0) {
      alert("최소 1개의 타겟 그룹을 선택해주세요");
      return;
    }

    const selected = archetypes.filter((a) =>
      selectedArchetypeIds.includes(a.segment_id)
    );

    setSavingArchetypes(true);
    try {
      // Save selected archetypes to backend (Multi-Archetype mode)
      const response = await fetch(
        `http://localhost:8000/api/workflows/${workflowId}/archetypes`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            archetypes: selected,
            currency: formData.currency,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to save archetypes");
      }

      // Navigate directly to confirm page
      router.push(`/workflows/${workflowId}/confirm`);
    } catch (error) {
      console.error("Error saving archetypes:", error);
      alert(error instanceof Error ? error.message : "아키타입 저장에 실패했습니다.");
    } finally {
      setSavingArchetypes(false);
    }
  };

  const toggleArchetypeSelection = (id: string) => {
    setSelectedArchetypeIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      // Convert percentages from 0-100 to 0-1 float for backend
      const requestData = {
        ...formData,
        gender_distribution: {
          female: formData.gender_distribution.female / 100,
          male: formData.gender_distribution.male / 100,
        },
        income_brackets: {
          none: (formData.income_brackets.none ?? 0) / 100,
          low: (formData.income_brackets.low ?? 0) / 100,
          mid: (formData.income_brackets.mid ?? 0) / 100,
          high: (formData.income_brackets.high ?? 0) / 100,
        },
        currency: formData.currency,
      };

      const response = await fetch(
        `http://localhost:8000/api/workflows/${workflowId}/persona`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(requestData),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error("API Error:", errorData);
        throw new Error(errorData.detail || "Failed to save persona");
      }

      router.push(`/workflows/${workflowId}/confirm`);
    } catch (error) {
      console.error("Error saving persona:", error);
      alert(error instanceof Error ? error.message : "Failed to save persona");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => router.push(`/workflows/${workflowId}/product`)}
        className="mb-2"
      >
        <ArrowLeft className="h-4 w-4 mr-2" />
        제품 정보 수정
      </Button>

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Step 2: 핵심 페르소나 정의</h1>
        <div className="text-sm text-muted-foreground">7단계 중 2단계</div>
      </div>

      {dataLoaded && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <span className="text-green-600 font-semibold">✓ 이전 설정 불러옴</span>
            <span className="text-sm text-green-700">
              이전에 입력했던 페르소나 정보가 자동으로 채워졌습니다. 수정 후 저장하세요.
            </span>
          </div>
        </div>
      )}

      <Card className="border-2 border-blue-200 bg-blue-50/30">
        <CardHeader>
          <CardTitle>💡 Gemini 시장조사로 페르소나 자동 완성</CardTitle>
          <p className="text-sm text-muted-foreground pt-2">
            3단계 프로세스: ① 프롬프트 생성 → ② Gemini에서 실행 → ③ 결과 붙여넣기 → 페르소나 자동 완성!
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <Tabs defaultValue="report" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="prompt">1️⃣ 프롬프트 생성/복사</TabsTrigger>
              <TabsTrigger value="report">2️⃣ 결과 붙여넣기</TabsTrigger>
            </TabsList>

            <TabsContent value="prompt" className="space-y-3 mt-4">
              {!researchPrompt ? (
                <div className="text-center py-6">
                  <Button
                    onClick={handleGenerateResearchPrompt}
                    disabled={generatingPrompt}
                    size="lg"
                    className="px-8"
                  >
                    {generatingPrompt ? (
                      <>
                        <span className="inline-block animate-spin mr-2">⏳</span>
                        프롬프트 생성 중...
                      </>
                    ) : (
                      "🔮 시장조사 프롬프트 생성하기"
                    )}
                  </Button>
                  <p className="text-xs text-muted-foreground mt-2">
                    제품 정보를 바탕으로 시장조사 프롬프트를 만듭니다 (무료 - API 비용 없음)
                  </p>
                </div>
              ) : (
                <>
                  <div className="bg-amber-50 border border-amber-200 rounded p-3 text-sm">
                    <p className="font-semibold text-amber-900">다음 단계:</p>
                    <ol className="list-decimal list-inside space-y-1 text-amber-800 mt-1">
                      <li>아래 프롬프트를 복사하세요</li>
                      <li>Gemini Deep Research (gemini.google.com)에 접속하세요</li>
                      <li>프롬프트를 붙여넣고 실행하세요</li>
                      <li>결과가 나오면 "2️⃣ 결과 붙여넣기" 탭으로 이동하세요</li>
                    </ol>
                  </div>
                  <Textarea
                    value={researchPrompt}
                    readOnly
                    rows={12}
                    className="font-mono text-sm"
                  />
                  <Button
                    onClick={() => {
                      navigator.clipboard.writeText(researchPrompt);
                      alert("✓ 프롬프트가 클립보드에 복사되었습니다!");
                    }}
                    className="w-full"
                    size="lg"
                  >
                    📋 프롬프트 복사하기
                  </Button>
                </>
              )}
            </TabsContent>

            <TabsContent value="report" className="space-y-3 mt-4">
                {!showArchetypeSelection ? (
                  <>
                    <div className="bg-green-50 border border-green-200 rounded p-3 text-sm">
                      <p className="font-semibold text-green-900">
                        Gemini 리서치 결과를 아래에 붙여넣으세요
                      </p>
                      <p className="text-green-800 mt-1">
                        AI가 3~5개의 타겟 고객 그룹을 추출합니다. 원하는 그룹을 선택하세요!
                      </p>
                    </div>
                    <Textarea
                      value={researchReport}
                      onChange={(e) => setResearchReport(e.target.value)}
                      placeholder="Gemini Deep Research 결과를 여기에 붙여넣으세요..."
                      rows={12}
                      className="text-sm"
                    />
                    {parsingReport && (
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">분석 진행률</span>
                          <span className="font-semibold">{parsingProgress}%</span>
                        </div>
                        <Progress value={parsingProgress} />
                      </div>
                    )}
                    <Button
                      onClick={handleParseResearchReport}
                      disabled={parsingReport || !researchReport.trim()}
                      className="w-full"
                      size="lg"
                    >
                      {parsingReport
                        ? `분석 중... (${parsingProgress}%)`
                        : "✨ 리서치 결과 분석하고 타겟 그룹 추출"}
                    </Button>
                  </>
                ) : (
                  <>
                    <div className="bg-purple-50 border border-purple-200 rounded p-3 text-sm">
                      <p className="font-semibold text-purple-900">
                        🎯 {archetypes.length}개의 타겟 고객 그룹이 발견되었습니다!
                      </p>
                      <p className="text-purple-800 mt-1">
                        타겟으로 삼을 그룹을 선택하세요. 여러 개 선택 시 가중 평균이 적용됩니다.
                      </p>
                    </div>

                    <div className="grid grid-cols-1 gap-3">
                      {archetypes.map((arch) => (
                        <div
                          key={arch.segment_id}
                          onClick={() => toggleArchetypeSelection(arch.segment_id)}
                          className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                            selectedArchetypeIds.includes(arch.segment_id)
                              ? "border-purple-500 bg-purple-50"
                              : "border-gray-200 hover:border-purple-300"
                          }`}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <span className="text-lg font-semibold">
                                  {arch.segment_name}
                                </span>
                                <span className="px-2 py-0.5 text-xs font-medium bg-gray-100 rounded-full">
                                  점유율 {Math.round(arch.share_ratio * 100)}%
                                </span>
                              </div>
                              <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-sm text-gray-600">
                                <div>
                                  <span className="font-medium">연령:</span>{" "}
                                  {arch.demographics.age_range[0]}~{arch.demographics.age_range[1]}세
                                </div>
                                <div>
                                  <span className="font-medium">성별:</span>{" "}
                                  여 {arch.demographics.gender_distribution.female}% / 남{" "}
                                  {arch.demographics.gender_distribution.male}%
                                </div>
                                <div>
                                  <span className="font-medium">소득:</span>{" "}
                                  {arch.income_level === "high"
                                    ? "고소득"
                                    : arch.income_level === "mid"
                                    ? "중소득"
                                    : arch.income_level === "low"
                                    ? "저소득"
                                    : "무소득/학생"}
                                </div>
                                <div>
                                  <span className="font-medium">사용빈도:</span>{" "}
                                  {arch.category_usage === "high"
                                    ? "높음"
                                    : arch.category_usage === "medium"
                                    ? "보통"
                                    : "낮음"}
                                </div>
                              </div>
                              {arch.core_traits && arch.core_traits.length > 0 && (
                                <div className="mt-2 flex flex-wrap gap-1">
                                  {arch.core_traits.slice(0, 4).map((trait, i) => (
                                    <span
                                      key={i}
                                      className="px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded"
                                    >
                                      {trait}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                            <div
                              className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                                selectedArchetypeIds.includes(arch.segment_id)
                                  ? "border-purple-500 bg-purple-500"
                                  : "border-gray-300"
                              }`}
                            >
                              {selectedArchetypeIds.includes(arch.segment_id) && (
                                <span className="text-white text-sm">✓</span>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="flex gap-2 pt-2">
                      <Button
                        onClick={() => {
                          setShowArchetypeSelection(false);
                          setArchetypes([]);
                        }}
                        variant="outline"
                        className="flex-1"
                        disabled={savingArchetypes}
                      >
                        ← 다시 분석
                      </Button>
                      <Button
                        onClick={handleApplyArchetypes}
                        disabled={selectedArchetypeIds.length === 0 || savingArchetypes}
                        className="flex-1"
                      >
                        {savingArchetypes
                          ? "저장 중..."
                          : selectedArchetypeIds.length === 0
                          ? "그룹을 선택하세요"
                          : `${selectedArchetypeIds.length}개 그룹으로 진행 →`}
                      </Button>
                    </div>
                  </>
                )}
              </TabsContent>
            </Tabs>

          {researchPrompt && (
            <div className="pt-2 border-t">
              <Button
                onClick={() => {
                  if (confirm("프롬프트를 다시 생성하시겠습니까? (이전 프롬프트는 삭제됩니다)")) {
                    setResearchPrompt("");
                    setResearchReport("");
                  }
                }}
                variant="outline"
                size="sm"
                className="w-full"
              >
                🔄 프롬프트 다시 생성하기
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 아키타입 선택 화면이 표시되면 수동 입력 폼 숨김 */}
      {!showArchetypeSelection && (
      <Card>
        <CardHeader>
          <CardTitle>또는: 수동으로 페르소나 작성 (7개 필수 항목)</CardTitle>
          <p className="text-sm text-muted-foreground pt-2">
            시장조사 결과 없이 직접 타겟 고객을 정의하려면 아래 항목을 입력하세요.
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>나이 범위 *</Label>
              <p className="text-sm text-muted-foreground">
                타겟 고객의 나이 범위를 설정하세요 (예: 25세 ~ 45세)
              </p>
              <div className="flex gap-2 items-center">
                <Input
                  type="number"
                  min="18"
                  max="100"
                  value={formData.age_range[0]}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      age_range: [Number.parseInt(e.target.value) || 18, formData.age_range[1]],
                    })
                  }
                  placeholder="최소"
                  className="w-24"
                />
                <span className="text-muted-foreground">~</span>
                <Input
                  type="number"
                  min="18"
                  max="100"
                  value={formData.age_range[1]}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      age_range: [formData.age_range[0], Number.parseInt(e.target.value) || 65],
                    })
                  }
                  placeholder="최대"
                  className="w-24"
                />
                <span className="text-sm text-muted-foreground">세</span>
              </div>
            </div>

            <div className="space-y-2">
              <Label>거주 지역 *</Label>
              <p className="text-sm text-muted-foreground">
                주요 타겟 고객이 사는 지역 유형
              </p>
              <select
                value={formData.location}
                onChange={(e) =>
                  setFormData({ ...formData, location: e.target.value })
                }
                className="w-full border rounded p-2 h-10"
              >
                <option value="urban">도시 (서울, 부산 등 대도시)</option>
                <option value="suburban">중소도시 (수도권, 지방 중소도시)</option>
                <option value="rural">농어촌 지역</option>
                <option value="mixed">혼합 (전국 대상)</option>
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <Label>성별 분포 (%) *</Label>
            <p className="text-sm text-muted-foreground">
              타겟 고객의 성별 분포를 설정하세요. 합계가 100%가 되어야 합니다.
            </p>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <Label className="text-sm font-medium">여성</Label>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    value={formData.gender_distribution.female}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        gender_distribution: {
                          ...formData.gender_distribution,
                          female: Number.parseInt(e.target.value) || 0,
                        },
                      })
                    }
                    onFocus={handleNumberInputFocus}
                    className="w-20"
                  />
                  <span className="text-sm text-muted-foreground">%</span>
                </div>
              </div>
              <div className="space-y-1">
                <Label className="text-sm font-medium">남성</Label>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    value={formData.gender_distribution.male}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        gender_distribution: {
                          ...formData.gender_distribution,
                          male: Number.parseInt(e.target.value) || 0,
                        },
                      })
                    }
                    onFocus={handleNumberInputFocus}
                    className="w-20"
                  />
                  <span className="text-sm text-muted-foreground">%</span>
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">
                현재 합계: {formData.gender_distribution.female + formData.gender_distribution.male}%
              </span>
              {formData.gender_distribution.female + formData.gender_distribution.male !== 100 && (
                <span className="text-destructive font-medium">⚠ 합계가 100%가 되어야 합니다</span>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <Label>통화 설정 *</Label>
            <p className="text-sm text-muted-foreground">
              소득 단위를 선택하세요. 통화에 따라 시스템 프롬프트 언어가 변경됩니다.
            </p>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="currency"
                  value="KRW"
                  checked={formData.currency === "KRW"}
                  onChange={() => setFormData({ ...formData, currency: "KRW" })}
                  className="w-4 h-4"
                />
                <span className="font-medium">🇰🇷 KRW (원)</span>
                <span className="text-sm text-muted-foreground">- 한국어 프롬프트</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="currency"
                  value="USD"
                  checked={formData.currency === "USD"}
                  onChange={() => setFormData({ ...formData, currency: "USD" })}
                  className="w-4 h-4"
                />
                <span className="font-medium">🇺🇸 USD ($)</span>
                <span className="text-sm text-muted-foreground">- 영어 프롬프트</span>
              </label>
            </div>
          </div>

          <div className="space-y-2">
            <Label>소득 분포 (%) *</Label>
            <p className="text-sm text-muted-foreground">
              타겟 고객의 소득 수준 분포를 설정하세요. 합계가 100%가 되어야 합니다.
              {formData.currency === "KRW" ? " (월 가처분 소득 기준)" : " (Monthly disposable income)"}
            </p>
            <div className="grid grid-cols-4 gap-4">
              <div className="space-y-1">
                <Label className="text-sm font-medium">
                  {formData.currency === "KRW" ? "무소득/학생" : "Minimal"}
                </Label>
                <p className="text-xs text-muted-foreground">
                  {formData.currency === "KRW" ? "0~50만원" : "$0-$500"}
                </p>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    value={formData.income_brackets.none ?? 0}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        income_brackets: {
                          ...formData.income_brackets,
                          none: parseInt(e.target.value) || 0,
                        },
                      })
                    }
                    onFocus={handleNumberInputFocus}
                    className="w-20"
                  />
                  <span className="text-sm text-muted-foreground">%</span>
                </div>
              </div>
              <div className="space-y-1">
                <Label className="text-sm font-medium">
                  {formData.currency === "KRW" ? "저소득" : "Low"}
                </Label>
                <p className="text-xs text-muted-foreground">
                  {formData.currency === "KRW" ? "50~150만원" : "$500-$2,000"}
                </p>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    value={formData.income_brackets.low ?? 0}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        income_brackets: {
                          ...formData.income_brackets,
                          low: parseInt(e.target.value) || 0,
                        },
                      })
                    }
                    onFocus={handleNumberInputFocus}
                    className="w-20"
                  />
                  <span className="text-sm text-muted-foreground">%</span>
                </div>
              </div>
              <div className="space-y-1">
                <Label className="text-sm font-medium">
                  {formData.currency === "KRW" ? "중소득" : "Middle"}
                </Label>
                <p className="text-xs text-muted-foreground">
                  {formData.currency === "KRW" ? "150~300만원" : "$2,000-$5,000"}
                </p>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    value={formData.income_brackets.mid ?? 0}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        income_brackets: {
                          ...formData.income_brackets,
                          mid: parseInt(e.target.value) || 0,
                        },
                      })
                    }
                    onFocus={handleNumberInputFocus}
                    className="w-20"
                  />
                  <span className="text-sm text-muted-foreground">%</span>
                </div>
              </div>
              <div className="space-y-1">
                <Label className="text-sm font-medium">
                  {formData.currency === "KRW" ? "고소득" : "High"}
                </Label>
                <p className="text-xs text-muted-foreground">
                  {formData.currency === "KRW" ? "300만원 이상" : "$5,000+"}
                </p>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    value={formData.income_brackets.high ?? 0}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        income_brackets: {
                          ...formData.income_brackets,
                          high: parseInt(e.target.value) || 0,
                        },
                      })
                    }
                    onFocus={handleNumberInputFocus}
                    className="w-20"
                  />
                  <span className="text-sm text-muted-foreground">%</span>
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">
                현재 합계: {(formData.income_brackets.none ?? 0) + (formData.income_brackets.low ?? 0) + (formData.income_brackets.mid ?? 0) + (formData.income_brackets.high ?? 0)}%
              </span>
              {(formData.income_brackets.none ?? 0) + (formData.income_brackets.low ?? 0) + (formData.income_brackets.mid ?? 0) + (formData.income_brackets.high ?? 0) !== 100 && (
                <span className="text-destructive font-medium">⚠ 합계가 100%가 되어야 합니다</span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>제품 카테고리 사용 빈도 *</Label>
              <p className="text-sm text-muted-foreground">
                이 제품 카테고리를 얼마나 자주 사용하나요?
              </p>
              <select
                value={formData.category_usage}
                onChange={(e) =>
                  setFormData({ ...formData, category_usage: e.target.value })
                }
                className="w-full border rounded p-2 h-10"
              >
                <option value="high">높음 (매일 사용)</option>
                <option value="medium">보통 (주 1~2회)</option>
                <option value="low">낮음 (가끔 사용)</option>
              </select>
            </div>

            <div className="space-y-2">
              <Label>쇼핑 성향 *</Label>
              <p className="text-sm text-muted-foreground">
                구매 결정 시 주요 성향은?
              </p>
              <select
                value={formData.shopping_behavior}
                onChange={(e) =>
                  setFormData({ ...formData, shopping_behavior: e.target.value })
                }
                className="w-full border rounded p-2 h-10"
              >
                <option value="smart_shopper">신중형 (꼼꼼히 비교)</option>
                <option value="quality">품질 중시형</option>
                <option value="budget">가격 중시형</option>
                <option value="impulsive">충동 구매형</option>
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <Label>주요 불편사항 (Pain Points) *</Label>
            <p className="text-sm text-muted-foreground">
              타겟 고객이 현재 겪고 있는 문제점이나 불편사항을 입력하세요 (예: "시간 관리가 어려움", "정보가 너무 많아 혼란스러움")
            </p>
            <div className="flex gap-2">
              <Input
                value={painPointInput}
                onChange={(e) => setPainPointInput(e.target.value)}
                placeholder="예: 업무 우선순위 설정이 어렵다"
                onKeyPress={(e) => e.key === "Enter" && handleAddPainPoint()}
              />
              <Button onClick={handleAddPainPoint} variant="outline">
                추가
              </Button>
            </div>
            <div className="space-y-1">
              {formData.key_pain_points.map((point, index) => (
                <div
                  key={`pain-${index}-${point}`}
                  className="flex items-center justify-between bg-muted p-2 rounded"
                >
                  <span className="text-sm">{point}</span>
                  <Button
                    onClick={() => handleRemovePainPoint(index)}
                    variant="ghost"
                    size="sm"
                  >
                    삭제
                  </Button>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <Label>구매 결정 요인 (Decision Drivers) *</Label>
            <p className="text-sm text-muted-foreground">
              고객이 제품 구매를 결정할 때 중요하게 생각하는 요소를 입력하세요 (예: "가성비", "사용 편의성", "브랜드 신뢰도")
            </p>
            <div className="flex gap-2">
              <Input
                value={driverInput}
                onChange={(e) => setDriverInput(e.target.value)}
                placeholder="예: 업무 효율성 향상"
                onKeyPress={(e) => e.key === "Enter" && handleAddDriver()}
              />
              <Button onClick={handleAddDriver} variant="outline">
                추가
              </Button>
            </div>
            <div className="space-y-1">
              {formData.decision_drivers.map((driver, index) => (
                <div
                  key={`driver-${index}-${driver}`}
                  className="flex items-center justify-between bg-muted p-2 rounded"
                >
                  <span className="text-sm">{driver}</span>
                  <Button
                    onClick={() => handleRemoveDriver(index)}
                    variant="ghost"
                    size="sm"
                  >
                    삭제
                  </Button>
                </div>
              ))}
            </div>
          </div>

          <Button
            onClick={handleSubmit}
            disabled={
              loading ||
              formData.key_pain_points.length === 0 ||
              formData.decision_drivers.length === 0 ||
              formData.gender_distribution.female + formData.gender_distribution.male !== 100 ||
              (formData.income_brackets.none ?? 0) + (formData.income_brackets.low ?? 0) + (formData.income_brackets.mid ?? 0) + (formData.income_brackets.high ?? 0) !== 100
            }
            className="w-full"
            size="lg"
          >
            {loading ? "저장 중..." : "✓ 페르소나 확정하고 다음 단계로"}
          </Button>
          {(formData.gender_distribution.female + formData.gender_distribution.male !== 100 ||
            (formData.income_brackets.none ?? 0) + (formData.income_brackets.low ?? 0) + (formData.income_brackets.mid ?? 0) + (formData.income_brackets.high ?? 0) !== 100) && (
            <p className="text-sm text-destructive text-center">
              ⚠ 성별 분포와 소득 분포의 합계가 각각 100%가 되어야 합니다
            </p>
          )}
        </CardContent>
      </Card>
      )}
    </div>
  );
}

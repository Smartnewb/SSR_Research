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
  const [showResearchModal, setShowResearchModal] = useState(false);

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

          setFormData({
            age_range: personaData.age_range || [25, 45],
            gender_distribution: convertToPercentage(
              personaData.gender_distribution || { female: 0.5, male: 0.5 }
            ),
            income_brackets: convertToPercentage(
              personaData.income_brackets || { none: 0.1, low: 0.25, mid: 0.45, high: 0.2 }
            ),
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
    try {
      const workflowResponse = await fetch(
        `http://localhost:8000/api/workflows/${workflowId}`
      );
      const workflow = await workflowResponse.json();

      if (!workflow.product) {
        alert("제품 설명을 먼저 입력해주세요");
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
            none: formData.income_brackets.none / 100,
            low: formData.income_brackets.low / 100,
            mid: formData.income_brackets.mid / 100,
            high: formData.income_brackets.high / 100,
          },
          location: formData.location,
          category_usage: formData.category_usage,
          shopping_behavior: formData.shopping_behavior,
          key_pain_points: formData.key_pain_points,
          decision_drivers: formData.decision_drivers,
        };
      }

      const response = await fetch(
        "http://localhost:8000/api/research/generate-prompt?use_mock=true",
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
    }
  };

  const handleParseResearchReport = async () => {
    if (!researchReport.trim()) {
      alert("Please paste your research report");
      return;
    }

    setParsingReport(true);
    setParsingProgress(10);
    try {
      setParsingProgress(30);
      const response = await fetch(
        "http://localhost:8000/api/research/parse-report?use_mock=false",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            research_report: researchReport,
          }),
        }
      );

      setParsingProgress(70);

      if (!response.ok) {
        throw new Error("Failed to parse research report");
      }

      const data = await response.json();
      setParsingProgress(90);

      // Normalize gender_distribution to ensure sum is exactly 100
      const normalizePercentages = (obj: Record<string, number>) => {
        const entries = Object.entries(obj).map(([k, v]) => [k, (v as number) * 100]);
        const sum = entries.reduce((acc, [_, v]) => acc + (v as number), 0);

        if (sum === 0) return Object.fromEntries(entries);

        // Normalize to 100%
        const normalized = entries.map(([k, v]) => [k, ((v as number) / sum) * 100]);

        // Round and adjust the largest value to ensure exact 100
        const rounded = normalized.map(([k, v]) => [k, Math.round(v as number)]);
        const roundedSum = rounded.reduce((acc, [_, v]) => acc + (v as number), 0);

        if (roundedSum !== 100 && rounded.length > 0) {
          // Find the largest value and adjust it
          const maxIndex = rounded.reduce(
            (maxIdx, [_, v], idx, arr) =>
              (v as number) > (arr[maxIdx][1] as number) ? idx : maxIdx,
            0
          );
          rounded[maxIndex][1] = (rounded[maxIndex][1] as number) + (100 - roundedSum);
        }

        return Object.fromEntries(rounded);
      };

      setFormData({
        age_range: data.refined_demographics.age_range,
        gender_distribution: normalizePercentages(data.refined_demographics.gender_distribution),
        income_brackets: normalizePercentages(data.refined_demographics.income_brackets),
        location: data.refined_demographics.location,
        category_usage: data.behavioral_insights.category_usage,
        shopping_behavior: data.behavioral_insights.shopping_behavior,
        key_pain_points: data.psychographics.key_pain_points,
        decision_drivers: data.psychographics.decision_drivers,
      });

      setParsingProgress(100);
      setShowResearchModal(false);
      alert(
        `Research insights applied! Confidence: ${data.confidence_score * 100}%`
      );
    } catch (error) {
      console.error("Error parsing report:", error);
      alert("Failed to parse research report");
    } finally {
      setParsingReport(false);
      setParsingProgress(0);
    }
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
          none: formData.income_brackets.none / 100,
          low: formData.income_brackets.low / 100,
          mid: formData.income_brackets.mid / 100,
          high: formData.income_brackets.high / 100,
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
          {!researchPrompt ? (
            <div className="text-center py-6">
              <Button
                onClick={handleGenerateResearchPrompt}
                size="lg"
                className="px-8"
              >
                1️⃣ 시장조사 프롬프트 생성하기
              </Button>
              <p className="text-xs text-muted-foreground mt-2">
                제품 정보를 바탕으로 시장조사 프롬프트를 만듭니다 (무료 - API 비용 없음)
              </p>
            </div>
          ) : (
            <Tabs defaultValue="prompt" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="prompt">2️⃣ 프롬프트 복사</TabsTrigger>
                <TabsTrigger value="report">3️⃣ 결과 붙여넣기</TabsTrigger>
              </TabsList>

              <TabsContent value="prompt" className="space-y-3 mt-4">
                <div className="bg-amber-50 border border-amber-200 rounded p-3 text-sm">
                  <p className="font-semibold text-amber-900">다음 단계:</p>
                  <ol className="list-decimal list-inside space-y-1 text-amber-800 mt-1">
                    <li>아래 프롬프트를 복사하세요</li>
                    <li>Gemini Deep Research (gemini.google.com)에 접속하세요</li>
                    <li>프롬프트를 붙여넣고 실행하세요</li>
                    <li>결과가 나오면 "3️⃣ 결과 붙여넣기" 탭으로 이동하세요</li>
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
              </TabsContent>

              <TabsContent value="report" className="space-y-3 mt-4">
                <div className="bg-green-50 border border-green-200 rounded p-3 text-sm">
                  <p className="font-semibold text-green-900">
                    Gemini 리서치 결과를 아래에 붙여넣으세요
                  </p>
                  <p className="text-green-800 mt-1">
                    AI가 자동으로 분석하여 아래의 7개 페르소나 필드를 채워드립니다!
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
                    : "✨ 리서치 결과 분석하고 페르소나 자동 완성"}
                </Button>
              </TabsContent>
            </Tabs>
          )}

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

      <Card>
        <CardHeader>
          <CardTitle>타겟 고객 페르소나 작성 (7개 필수 항목)</CardTitle>
          <p className="text-sm text-muted-foreground pt-2">
            아래 항목을 직접 입력하거나, 위의 시장조사 결과를 통해 자동으로 채울 수 있습니다.
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
                  {formData.currency === "KRW" ? "0~30만원" : "$0-$500"}
                </p>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    value={formData.income_brackets.none}
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
                  {formData.currency === "KRW" ? "30~70만원" : "$500-$2,000"}
                </p>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    value={formData.income_brackets.low}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        income_brackets: {
                          ...formData.income_brackets,
                          low: Number.parseInt(e.target.value) || 0,
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
                  {formData.currency === "KRW" ? "70~120만원" : "$2,000-$5,000"}
                </p>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    value={formData.income_brackets.mid}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        income_brackets: {
                          ...formData.income_brackets,
                          mid: Number.parseInt(e.target.value) || 0,
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
                  {formData.currency === "KRW" ? "120~200만원" : "$5,000-$10,000"}
                </p>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    value={formData.income_brackets.high}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        income_brackets: {
                          ...formData.income_brackets,
                          high: Number.parseInt(e.target.value) || 0,
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
                현재 합계: {formData.income_brackets.none + formData.income_brackets.low + formData.income_brackets.mid + formData.income_brackets.high}%
              </span>
              {formData.income_brackets.none + formData.income_brackets.low + formData.income_brackets.mid + formData.income_brackets.high !== 100 && (
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
              formData.income_brackets.none + formData.income_brackets.low + formData.income_brackets.mid + formData.income_brackets.high !== 100
            }
            className="w-full"
            size="lg"
          >
            {loading ? "저장 중..." : "✓ 페르소나 확정하고 다음 단계로"}
          </Button>
          {(formData.gender_distribution.female + formData.gender_distribution.male !== 100 ||
            formData.income_brackets.none + formData.income_brackets.low + formData.income_brackets.mid + formData.income_brackets.high !== 100) && (
            <p className="text-sm text-destructive text-center">
              ⚠ 성별 분포와 소득 분포의 합계가 각각 100%가 되어야 합니다
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

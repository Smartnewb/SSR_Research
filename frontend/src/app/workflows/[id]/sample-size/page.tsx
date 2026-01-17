"use client";

import { useParams, useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, Users, Zap, Target, Info } from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

// Sample size presets with scale strategy
const SAMPLE_SIZES = [
  {
    value: 30,
    scale: "debug",
    cost: "$0.06",
    time: "< 1 min",
    description: "Quick validation",
  },
  {
    value: 100,
    scale: "pilot",
    cost: "$0.20",
    time: "1 min",
    description: "Initial testing",
  },
  {
    value: 300,
    scale: "pilot",
    cost: "$0.60",
    time: "3 min",
    description: "Trend analysis",
  },
  {
    value: 1000,
    scale: "standard",
    cost: "$2.00",
    time: "8 min",
    description: "Statistically significant (Recommended)",
  },
  {
    value: 5000,
    scale: "massive",
    cost: "$10.00",
    time: "40 min",
    description: "Large-scale simulation",
  },
  {
    value: 10000,
    scale: "massive",
    cost: "$20.00",
    time: "80 min",
    description: "Maximum precision",
  },
];

interface Archetype {
  segment_id?: string;
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

// Default archetypes for demonstration
const DEFAULT_ARCHETYPES: Archetype[] = [
  {
    segment_id: "SEGMENT_01",
    segment_name: "가성비 중시형",
    share_ratio: 0.4,
    demographics: {
      age_range: [19, 25],
      gender_distribution: { female: 55, male: 45 },
    },
    income_level: "low",
    category_usage: "medium",
    shopping_behavior: "price_sensitive",
    core_traits: ["가격 민감", "비교 쇼핑"],
    pain_points: ["예산 부족", "가성비 고민"],
    decision_drivers: ["가격", "후기"],
  },
  {
    segment_id: "SEGMENT_02",
    segment_name: "품질 중시형",
    share_ratio: 0.3,
    demographics: {
      age_range: [25, 35],
      gender_distribution: { female: 60, male: 40 },
    },
    income_level: "mid",
    category_usage: "high",
    shopping_behavior: "quality",
    core_traits: ["품질 우선", "브랜드 선호"],
    pain_points: ["품질 불확실성", "가품 걱정"],
    decision_drivers: ["품질", "브랜드 신뢰"],
  },
  {
    segment_id: "SEGMENT_03",
    segment_name: "충동 구매형",
    share_ratio: 0.2,
    demographics: {
      age_range: [20, 30],
      gender_distribution: { female: 65, male: 35 },
    },
    income_level: "mid",
    category_usage: "high",
    shopping_behavior: "impulsive",
    core_traits: ["트렌드 민감", "즉흥적"],
    pain_points: ["과소비 걱정", "후회"],
    decision_drivers: ["디자인", "트렌드"],
  },
  {
    segment_id: "SEGMENT_04",
    segment_name: "합리적 소비형",
    share_ratio: 0.1,
    demographics: {
      age_range: [28, 40],
      gender_distribution: { female: 50, male: 50 },
    },
    income_level: "high",
    category_usage: "medium",
    shopping_behavior: "smart_shopper",
    core_traits: ["정보 수집", "비교 분석"],
    pain_points: ["시간 부족", "정보 과부하"],
    decision_drivers: ["가치", "효율성"],
  },
];

export default function SampleSizePage() {
  const params = useParams();
  const router = useRouter();
  const workflowId = params.id as string;

  const [selectedSize, setSelectedSize] = useState(1000);
  const [loading, setLoading] = useState(false);
  const [useMultiArchetype, setUseMultiArchetype] = useState(false);
  const [archetypes, setArchetypes] = useState<Archetype[]>([]);
  const [enrich, setEnrich] = useState(true);

  // Load workflow data to check if archetypes exist
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

        // Step 2에서 archetype을 만들었으면 자동 활성화
        if (workflow.archetypes?.length > 0) {
          setUseMultiArchetype(true);
          setArchetypes(workflow.archetypes);
        } else {
          // archetype이 없으면 기본값 사용 (단일 persona 모드)
          setArchetypes(DEFAULT_ARCHETYPES);
        }
      }
    } catch (error) {
      console.error("Error loading workflow data:", error);
      setArchetypes(DEFAULT_ARCHETYPES);
    }
  };

  // Calculate distribution preview
  const distributionPreview = archetypes.map((arch) => ({
    ...arch,
    count: Math.round(selectedSize * arch.share_ratio),
  }));

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const requestBody: Record<string, unknown> = {
        sample_size: selectedSize,
        use_multi_archetype: useMultiArchetype,
        enrich: enrich,
      };

      if (useMultiArchetype) {
        requestBody.archetypes = archetypes;
      }

      const response = await fetch(
        `http://localhost:8000/api/workflows/${workflowId}/sample-size`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(requestBody),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to set sample size");
      }

      router.push(`/workflows/${workflowId}/generating`);
    } catch (error) {
      console.error("Error setting sample size:", error);
      alert("Failed to set sample size");
    } finally {
      setLoading(false);
    }
  };

  const getScaleColor = (scale: string) => {
    switch (scale) {
      case "debug":
        return "text-gray-500";
      case "pilot":
        return "text-blue-500";
      case "standard":
        return "text-green-600 font-semibold";
      case "massive":
        return "text-purple-500";
      default:
        return "";
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
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
        <h1 className="text-2xl font-bold">Step 4: Select Sample Size</h1>
        <div className="text-sm text-muted-foreground">Step 4 of 7</div>
      </div>

      {/* Multi-Archetype Toggle */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Target className="h-5 w-5 text-primary" />
              <CardTitle className="text-lg">
                Multi-Archetype Stratified Sampling
              </CardTitle>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <Info className="h-4 w-4 text-muted-foreground" />
                  </TooltipTrigger>
                  <TooltipContent className="max-w-xs">
                    <p>
                      시장을 여러 세그먼트로 나누어 각 그룹의 비율에 맞게
                      페르소나를 생성합니다. 더 현실적이고 다양한 데이터를 얻을
                      수 있습니다.
                    </p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
            <div className="flex items-center gap-2">
              <Label htmlFor="multi-archetype" className="text-sm">
                {useMultiArchetype ? "Enabled" : "Disabled"}
              </Label>
              <Switch
                id="multi-archetype"
                checked={useMultiArchetype}
                onCheckedChange={setUseMultiArchetype}
              />
            </div>
          </div>
          <p className="text-sm text-muted-foreground mt-2">
            {useMultiArchetype
              ? "여러 고객 유형(가성비 중시, 품질 중시 등)을 비율대로 생성하여 현실적인 시장을 반영합니다."
              : "활성화하면 단일 고객 유형 대신, 여러 고객 유형을 비율대로 나누어 더 다양한 페르소나를 생성합니다."}
          </p>
        </CardHeader>

        {useMultiArchetype && (
          <CardContent className="pt-0">
            <div className="bg-muted/30 rounded-lg p-4 space-y-3">
              <h4 className="font-medium text-sm flex items-center gap-2">
                <Users className="h-4 w-4" />
                Distribution Preview ({selectedSize.toLocaleString()} total)
              </h4>
              <div className="grid grid-cols-2 gap-2">
                {distributionPreview.map((arch, idx) => (
                  <div
                    key={idx}
                    className="flex justify-between items-center text-sm bg-background rounded px-3 py-2"
                  >
                    <span className="font-medium">{arch.segment_name}</span>
                    <span className="text-muted-foreground">
                      {arch.count.toLocaleString()}명 (
                      {(arch.share_ratio * 100).toFixed(0)}%)
                    </span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-muted-foreground">
                * GPT-5.2 (reasoning: high)로 시장 세분화 후, GPT-5-mini
                (verbosity: high)로 풍부한 페르소나 생성
              </p>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Sample Size Selection */}
      <Card>
        <CardHeader>
          <CardTitle>How many synthetic personas to generate?</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            {SAMPLE_SIZES.map((option) => (
              <div
                key={option.value}
                className={`border rounded-lg p-4 cursor-pointer transition ${
                  selectedSize === option.value
                    ? "border-primary bg-primary/5 ring-2 ring-primary/20"
                    : "hover:border-primary/50"
                }`}
                onClick={() => setSelectedSize(option.value)}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <input
                      type="radio"
                      checked={selectedSize === option.value}
                      onChange={() => setSelectedSize(option.value)}
                      className="accent-primary"
                    />
                    <span className="font-semibold">
                      {option.value.toLocaleString()}
                    </span>
                  </div>
                  <span className="text-lg font-bold text-primary">
                    {option.cost}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className={getScaleColor(option.scale)}>
                    {option.description}
                  </span>
                  <span className="text-muted-foreground">{option.time}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Enrichment Toggle */}
          <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-yellow-500" />
              <div>
                <span className="font-medium text-sm">LLM Enrichment</span>
                <p className="text-xs text-muted-foreground">
                  각 페르소나에 풍부한 배경 스토리 추가 (verbosity: high)
                </p>
              </div>
            </div>
            <Switch checked={enrich} onCheckedChange={setEnrich} />
          </div>

          <div className="bg-muted/50 p-4 rounded-lg space-y-2">
            <h4 className="font-semibold text-sm">Scale Strategy</h4>
            <div className="grid grid-cols-4 gap-2 text-xs">
              <div>
                <span className="text-gray-500 font-medium">Debug</span>
                <p className="text-muted-foreground">10-30명</p>
              </div>
              <div>
                <span className="text-blue-500 font-medium">Pilot</span>
                <p className="text-muted-foreground">100-300명</p>
              </div>
              <div>
                <span className="text-green-600 font-medium">Standard</span>
                <p className="text-muted-foreground">1,000명 (권장)</p>
              </div>
              <div>
                <span className="text-purple-500 font-medium">Massive</span>
                <p className="text-muted-foreground">5,000명+</p>
              </div>
            </div>
          </div>

          <Button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full"
            size="lg"
          >
            {loading ? (
              "Setting up..."
            ) : (
              <>
                Generate {selectedSize.toLocaleString()} Personas
                {useMultiArchetype && " (Multi-Archetype)"}
              </>
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

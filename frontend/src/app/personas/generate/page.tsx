"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Loader2,
  Users,
  BarChart3,
  Download,
  Play,
  Eye,
  CheckCircle,
  RefreshCw,
  Target,
  Info,
  Zap,
} from "lucide-react";
import { toast } from "sonner";
import {
  generatePersonas,
  previewPersonas,
  getCorePersona,
  getConcept,
  generateFromArchetypes,
  type GeneratePersonasResponse,
  type CorePersonaResponse,
  type ConceptResponse,
} from "@/lib/api";
import type { Archetype, ArchetypeGenerateResponse, GeneratedPersona } from "@/lib/types";

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

function GenerateContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const personaId = searchParams.get("persona_id");
  const conceptId = searchParams.get("concept_id");

  const [sampleSize, setSampleSize] = useState(100);
  const [randomSeed, setRandomSeed] = useState<number | undefined>(undefined);
  const [useFixedSeed, setUseFixedSeed] = useState(false);

  const [useMultiArchetype, setUseMultiArchetype] = useState(false);
  const [archetypes] = useState<Archetype[]>(DEFAULT_ARCHETYPES);
  const [enrich, setEnrich] = useState(true);

  const [isGenerating, setIsGenerating] = useState(false);
  const [isPreviewing, setIsPreviewing] = useState(false);

  const [previewData, setPreviewData] = useState<GeneratedPersona[]>([]);
  const [generationResult, setGenerationResult] = useState<GeneratePersonasResponse | null>(null);
  const [archetypeResult, setArchetypeResult] = useState<ArchetypeGenerateResponse | null>(null);

  const [corePersonaData, setCorePersonaData] = useState<CorePersonaResponse | null>(null);
  const [conceptData, setConceptData] = useState<ConceptResponse | null>(null);

  const [activeTab, setActiveTab] = useState("preview");

  const distributionPreview = archetypes.map((arch) => ({
    ...arch,
    count: Math.round(sampleSize * arch.share_ratio),
  }));

  useEffect(() => {
    loadPreview();
    loadMetadata();
  }, [personaId, conceptId]);

  const loadMetadata = async () => {
    if (personaId) {
      const persona = await getCorePersona(personaId);
      setCorePersonaData(persona);
    }
    if (conceptId) {
      const concept = await getConcept(conceptId);
      setConceptData(concept);
    }
  };

  const loadPreview = async () => {
    setIsPreviewing(true);
    try {
      const result = await previewPersonas(personaId || undefined, 5);
      setPreviewData(result.preview_personas);
    } catch (error) {
      console.error("Failed to load preview:", error);
    } finally {
      setIsPreviewing(false);
    }
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      if (useMultiArchetype) {
        const result = await generateFromArchetypes({
          archetypes,
          total_samples: sampleSize,
          product_context: conceptData?.title,
          currency: "KRW",
          enrich,
          random_seed: useFixedSeed ? randomSeed : undefined,
        });
        setArchetypeResult(result);
        setGenerationResult(null);
        setActiveTab("results");
        toast.success(`Generated ${result.total_count} personas across ${result.distribution_plan.length} segments!`);
      } else {
        const result = await generatePersonas({
          core_persona_id: personaId || undefined,
          sample_size: sampleSize,
          random_seed: useFixedSeed ? randomSeed : undefined,
        });
        setGenerationResult(result);
        setArchetypeResult(null);
        setActiveTab("results");
        toast.success(`Generated ${result.total_personas} personas!`);
      }
    } catch (error) {
      toast.error("Failed to generate personas");
      console.error(error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownload = () => {
    const result = generationResult || archetypeResult;
    if (!result) return;

    const exportData = {
      export_version: "2.0",
      exported_at: new Date().toISOString(),
      mode: archetypeResult ? "multi_archetype" : "single",
      core_persona: corePersonaData,
      concept: conceptData,
      generation: archetypeResult ? {
        total_count: archetypeResult.total_count,
        distribution_plan: archetypeResult.distribution_plan,
        stats: archetypeResult.stats,
        segment_stats: archetypeResult.segment_stats,
        enriched: archetypeResult.enriched,
        personas: archetypeResult.personas,
      } : generationResult,
    };

    const dataStr = JSON.stringify(exportData, null, 2);
    const blob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const timestamp = new Date().toISOString().split("T")[0];
    a.download = `personas_${archetypeResult ? "multi" : "single"}_${timestamp}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success("Downloaded personas JSON");
  };

  const handleRunSurvey = () => {
    const result = generationResult || archetypeResult;
    if (!result) return;

    // Store generation result in localStorage for survey page
    if (archetypeResult) {
      localStorage.setItem("generated_personas", JSON.stringify({
        job_id: `ARCHETYPE_${Date.now()}`,
        total_personas: archetypeResult.total_count,
        distribution_stats: archetypeResult.stats,
        personas: archetypeResult.personas,
      }));
    } else if (generationResult) {
      localStorage.setItem("generated_personas", JSON.stringify(generationResult));
    }
    router.push(`/surveys/new?generated=true${conceptId ? `&concept_id=${conceptId}` : ""}`);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Step 3: Generate Sample</h1>
        <p className="text-muted-foreground">
          Generate synthetic personas for your survey based on your core persona profile.
          <span className="flex gap-2 mt-2">
            {personaId && (
              <Badge variant="outline">Persona: {personaId}</Badge>
            )}
            {conceptId && (
              <Badge variant="outline">Concept: {conceptId}</Badge>
            )}
          </span>
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Settings Panel */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Generation Settings
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Multi-Archetype Toggle */}
            <div className="p-3 bg-muted/30 rounded-lg space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Target className="h-4 w-4 text-primary" />
                  <span className="font-medium text-sm">Multi-Archetype Mode</span>
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger>
                        <Info className="h-4 w-4 text-muted-foreground" />
                      </TooltipTrigger>
                      <TooltipContent className="max-w-xs">
                        <p>시장을 여러 세그먼트로 나누어 각 그룹의 비율에 맞게 페르소나를 생성합니다.</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>
                <Switch
                  checked={useMultiArchetype}
                  onCheckedChange={setUseMultiArchetype}
                />
              </div>
              {useMultiArchetype && (
                <div className="space-y-2 pt-2 border-t">
                  <p className="text-xs text-muted-foreground">Distribution Preview:</p>
                  {distributionPreview.map((arch) => (
                    <div key={arch.segment_id} className="flex justify-between text-xs">
                      <span>{arch.segment_name}</span>
                      <span className="text-muted-foreground">
                        {arch.count.toLocaleString()}명 ({(arch.share_ratio * 100).toFixed(0)}%)
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="space-y-3">
              <Label>Sample Size: {sampleSize.toLocaleString()}</Label>
              <Slider
                value={[sampleSize]}
                min={10}
                max={5000}
                step={10}
                onValueChange={(v) => setSampleSize(v[0])}
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>10 (Debug)</span>
                <span>5,000 (Massive)</span>
              </div>
            </div>

            {/* LLM Enrichment Toggle */}
            {useMultiArchetype && (
              <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                <div className="flex items-center gap-2">
                  <Zap className="h-4 w-4 text-yellow-500" />
                  <div>
                    <span className="font-medium text-sm">LLM Enrichment</span>
                    <p className="text-xs text-muted-foreground">풍부한 배경 스토리 추가</p>
                  </div>
                </div>
                <Switch checked={enrich} onCheckedChange={setEnrich} />
              </div>
            )}

            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="fixedSeed"
                  checked={useFixedSeed}
                  onChange={(e) => setUseFixedSeed(e.target.checked)}
                  className="rounded"
                />
                <Label htmlFor="fixedSeed">Use fixed random seed</Label>
              </div>
              {useFixedSeed && (
                <Input
                  type="number"
                  placeholder="Enter seed (e.g., 42)"
                  value={randomSeed ?? ""}
                  onChange={(e) => {
                    const val = e.target.value;
                    setRandomSeed(val === "" ? undefined : parseInt(val, 10));
                  }}
                />
              )}
              <p className="text-xs text-muted-foreground">
                Fixed seed ensures reproducible results for the same settings
              </p>
            </div>

            <div className="space-y-2 pt-4">
              <Button
                onClick={handleGenerate}
                disabled={isGenerating}
                className="w-full"
                size="lg"
              >
                {isGenerating ? (
                  <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Generating...</>
                ) : (
                  <><Play className="mr-2 h-4 w-4" /> Generate {sampleSize.toLocaleString()} Personas</>
                )}
              </Button>

              {generationResult && (
                <>
                  <Button
                    variant="outline"
                    onClick={handleDownload}
                    className="w-full"
                  >
                    <Download className="mr-2 h-4 w-4" /> Download JSON
                  </Button>
                  <Button
                    variant="default"
                    onClick={handleRunSurvey}
                    className="w-full"
                  >
                    <CheckCircle className="mr-2 h-4 w-4" /> Run Survey with These Personas
                  </Button>
                </>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Main Content */}
        <div className="lg:col-span-2">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="preview">
                <Eye className="mr-2 h-4 w-4" /> Preview
              </TabsTrigger>
              <TabsTrigger value="results" disabled={!generationResult && !archetypeResult}>
                <BarChart3 className="mr-2 h-4 w-4" /> Results
              </TabsTrigger>
            </TabsList>

            {/* Preview Tab */}
            <TabsContent value="preview" className="mt-4">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>Sample Preview (5 personas)</CardTitle>
                    <Button variant="ghost" size="sm" onClick={loadPreview} disabled={isPreviewing}>
                      <RefreshCw className={`h-4 w-4 ${isPreviewing ? "animate-spin" : ""}`} />
                    </Button>
                  </div>
                  <CardDescription>
                    Preview how generated personas will look
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {isPreviewing ? (
                    <div className="flex justify-center py-8">
                      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {previewData.map((persona, idx) => (
                        <Card key={idx} className="bg-muted/50">
                          <CardContent className="pt-4">
                            <div className="flex items-start justify-between">
                              <div>
                                <div className="flex items-center gap-2 mb-2">
                                  <Badge>{persona.gender}</Badge>
                                  <Badge variant="outline">{persona.age} years old</Badge>
                                  <Badge variant="secondary">{persona.income_bracket} income</Badge>
                                </div>
                                <p className="text-sm text-muted-foreground">
                                  {persona.location} • {persona.category_usage} category usage • {persona.shopping_behavior}
                                </p>
                              </div>
                              <span className="text-xs text-muted-foreground">{persona.id}</span>
                            </div>
                            <div className="mt-3 text-sm">
                              <p><strong>Pain points:</strong> {persona.pain_points.join(", ")}</p>
                              <p><strong>Decision drivers:</strong> {persona.decision_drivers.join(", ")}</p>
                            </div>
                            {persona.system_prompt && (
                              <details className="mt-3">
                                <summary className="text-xs text-muted-foreground cursor-pointer">
                                  View System Prompt
                                </summary>
                                <pre className="mt-2 p-2 bg-background rounded text-xs whitespace-pre-wrap">
                                  {persona.system_prompt}
                                </pre>
                              </details>
                            )}
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Results Tab */}
            <TabsContent value="results" className="mt-4 space-y-4">
              {/* Multi-Archetype Results */}
              {archetypeResult && (
                <>
                  {/* Segment Distribution */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Target className="h-5 w-5" />
                        Segment Distribution
                      </CardTitle>
                      <CardDescription>
                        Total: {archetypeResult.total_count.toLocaleString()} personas
                        {archetypeResult.enriched && (
                          <Badge variant="secondary" className="ml-2">
                            <Zap className="h-3 w-3 mr-1" />
                            Enriched
                          </Badge>
                        )}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 gap-3">
                        {archetypeResult.distribution_plan.map((plan) => (
                          <div key={plan.segment_id} className="p-3 bg-muted rounded-lg">
                            <div className="flex justify-between items-center">
                              <span className="font-medium">{plan.segment_name}</span>
                              <Badge variant="outline">{plan.count.toLocaleString()}명</Badge>
                            </div>
                            <div className="text-xs text-muted-foreground mt-1">
                              Target: {(plan.share_ratio * 100).toFixed(0)}% → Actual: {(plan.actual_ratio * 100).toFixed(1)}%
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Overall Stats */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Distribution Statistics</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-3 gap-4">
                        {archetypeResult.stats.age && (
                          <div className="p-4 bg-muted rounded-lg">
                            <h4 className="font-medium mb-2">Age Distribution</h4>
                            <div className="space-y-1 text-sm">
                              <p>Mean: {archetypeResult.stats.age.mean.toFixed(1)}</p>
                              <p>Std: {archetypeResult.stats.age.std.toFixed(1)}</p>
                              <p>Range: {archetypeResult.stats.age.min} - {archetypeResult.stats.age.max}</p>
                            </div>
                          </div>
                        )}
                        {archetypeResult.stats.gender && (
                          <div className="p-4 bg-muted rounded-lg">
                            <h4 className="font-medium mb-2">Gender Distribution</h4>
                            <div className="space-y-1 text-sm">
                              {Object.entries(archetypeResult.stats.gender).map(([k, v]) => (
                                <p key={k}>{k}: {v} ({((v / archetypeResult.total_count) * 100).toFixed(1)}%)</p>
                              ))}
                            </div>
                          </div>
                        )}
                        {archetypeResult.stats.income && (
                          <div className="p-4 bg-muted rounded-lg">
                            <h4 className="font-medium mb-2">Income Distribution</h4>
                            <div className="space-y-1 text-sm">
                              {Object.entries(archetypeResult.stats.income).map(([k, v]) => (
                                <p key={k}>{k}: {v} ({((v / archetypeResult.total_count) * 100).toFixed(1)}%)</p>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Personas Table with Segment */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Generated Personas ({archetypeResult.total_count})</CardTitle>
                      <CardDescription>
                        Showing first 20 of {archetypeResult.total_count} personas
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="max-h-96 overflow-auto">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Segment</TableHead>
                              <TableHead>Age</TableHead>
                              <TableHead>Gender</TableHead>
                              <TableHead>Income</TableHead>
                              <TableHead>Bio</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {archetypeResult.personas.slice(0, 20).map((p) => (
                              <TableRow key={p.id}>
                                <TableCell>
                                  <Badge variant="outline" className="text-xs">
                                    {p.segment_name}
                                  </Badge>
                                </TableCell>
                                <TableCell>{p.age}</TableCell>
                                <TableCell>{p.gender}</TableCell>
                                <TableCell>{p.income_bracket}</TableCell>
                                <TableCell className="max-w-xs truncate text-xs">
                                  {p.bio || "-"}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    </CardContent>
                  </Card>
                </>
              )}

              {/* Single Archetype Results */}
              {generationResult && !archetypeResult && (
                <>
                  {/* Distribution Stats */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Distribution Statistics</CardTitle>
                      <CardDescription>
                        Job ID: {generationResult.job_id}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-3 gap-4">
                        {/* Age Stats */}
                        {generationResult.distribution_stats.age && (
                          <div className="p-4 bg-muted rounded-lg">
                            <h4 className="font-medium mb-2">Age Distribution</h4>
                            <div className="space-y-1 text-sm">
                              <p>Mean: {generationResult.distribution_stats.age.mean.toFixed(1)}</p>
                              <p>Std: {generationResult.distribution_stats.age.std.toFixed(1)}</p>
                              <p>Range: {generationResult.distribution_stats.age.min} - {generationResult.distribution_stats.age.max}</p>
                            </div>
                          </div>
                        )}

                        {/* Gender Stats */}
                        {generationResult.distribution_stats.gender && (
                          <div className="p-4 bg-muted rounded-lg">
                            <h4 className="font-medium mb-2">Gender Distribution</h4>
                            <div className="space-y-1 text-sm">
                              {Object.entries(generationResult.distribution_stats.gender).map(([k, v]) => (
                                <p key={k}>{k}: {v} ({((v / generationResult.total_personas) * 100).toFixed(1)}%)</p>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Income Stats */}
                        {generationResult.distribution_stats.income && (
                          <div className="p-4 bg-muted rounded-lg">
                            <h4 className="font-medium mb-2">Income Distribution</h4>
                            <div className="space-y-1 text-sm">
                              {Object.entries(generationResult.distribution_stats.income).map(([k, v]) => (
                                <p key={k}>{k}: {v} ({((v / generationResult.total_personas) * 100).toFixed(1)}%)</p>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Personas Table */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Generated Personas ({generationResult.total_personas})</CardTitle>
                      <CardDescription>
                        Showing first 20 of {generationResult.total_personas} personas
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="max-h-96 overflow-auto">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>ID</TableHead>
                              <TableHead>Age</TableHead>
                              <TableHead>Gender</TableHead>
                              <TableHead>Income</TableHead>
                              <TableHead>Location</TableHead>
                              <TableHead>Usage</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {generationResult.personas.slice(0, 20).map((p) => (
                              <TableRow key={p.id}>
                                <TableCell className="font-mono text-xs">{p.id}</TableCell>
                                <TableCell>{p.age}</TableCell>
                                <TableCell>{p.gender}</TableCell>
                                <TableCell>{p.income_bracket}</TableCell>
                                <TableCell>{p.location}</TableCell>
                                <TableCell>{p.category_usage}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    </CardContent>
                  </Card>
                </>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}

export default function GeneratePage() {
  return (
    <Suspense fallback={<div className="flex justify-center py-8"><Loader2 className="h-8 w-8 animate-spin" /></div>}>
      <GenerateContent />
    </Suspense>
  );
}

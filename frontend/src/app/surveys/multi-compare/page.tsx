"use client";

import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import type { ConceptInput, MultiCompareResponse } from "@/lib/types";
import { Plus, Trash2, Play, RotateCcw } from "lucide-react";

export default function MultiComparePage() {
  const [concepts, setConcepts] = useState<ConceptInput[]>([
    {
      id: "CONCEPT_001",
      title: "",
      headline: "",
      consumer_insight: "",
      benefits: [""],
      rtb: [""],
      image_prompt: "",
      price: "",
    },
    {
      id: "CONCEPT_002",
      title: "",
      headline: "",
      consumer_insight: "",
      benefits: [""],
      rtb: [""],
      image_prompt: "",
      price: "",
    },
  ]);

  const [personaSetId, setPersonaSetId] = useState("default_personas");
  const [sampleSize, setSampleSize] = useState(100);
  const [comparisonMode, setComparisonMode] = useState<"rank_based" | "absolute">("rank_based");
  const [useMock, setUseMock] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [targetProgress, setTargetProgress] = useState(0);
  const [results, setResults] = useState<MultiCompareResponse | null>(null);
  const animationRef = useRef<number | null>(null);

  useEffect(() => {
    if (!isRunning) return;

    const animate = () => {
      setProgress((prev) => {
        const diff = targetProgress - prev;
        if (Math.abs(diff) < 0.1) return targetProgress;
        return prev + diff * 0.08;
      });
      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isRunning, targetProgress]);

  const addConcept = () => {
    if (concepts.length >= 5) {
      toast.error("Maximum 5 concepts allowed");
      return;
    }
    setConcepts([
      ...concepts,
      {
        id: `CONCEPT_${String(concepts.length + 1).padStart(3, "0")}`,
        title: "",
        headline: "",
        consumer_insight: "",
        benefits: [""],
        rtb: [""],
        image_prompt: "",
        price: "",
      },
    ]);
  };

  const removeConcept = (index: number) => {
    if (concepts.length <= 2) {
      toast.error("Minimum 2 concepts required");
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
      if (!concept.title || !concept.headline || !concept.consumer_insight ||
          !concept.benefits?.some(b => b.trim()) || !concept.rtb?.some(r => r.trim()) ||
          !concept.image_prompt || !concept.price) {
        toast.error("Please fill all fields for all concepts");
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
      toast.error("Maximum 5 items allowed");
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
      toast.error("At least 1 item required");
      return;
    }
    list.splice(itemIndex, 1);
    updated[conceptIndex] = { ...updated[conceptIndex], [field]: list };
    setConcepts(updated);
  };

  const handleSubmit = async () => {
    if (!validateConcepts()) return;

    try {
      setIsRunning(true);
      setProgress(0);
      setTargetProgress(0);

      const progressInterval = setInterval(() => {
        setTargetProgress((prev) => Math.min(prev + 2, 90));
      }, 200);

      const response = await fetch("http://localhost:8000/api/surveys/multi-compare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          concepts,
          persona_set_id: personaSetId,
          sample_size: sampleSize,
          comparison_mode: comparisonMode,
          use_mock: useMock,
        }),
      });

      clearInterval(progressInterval);

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Comparison failed");
      }

      const result: MultiCompareResponse = await response.json();
      setTargetProgress(100);
      setTimeout(() => {
        setProgress(100);
        setResults(result);
        setIsRunning(false);
        toast.success("Multi-concept comparison completed!");
      }, 300);
    } catch (error) {
      setIsRunning(false);
      setProgress(0);
      setTargetProgress(0);
      toast.error(error instanceof Error ? error.message : "Failed to run comparison");
      console.error(error);
    }
  };

  const handleReset = () => {
    setResults(null);
    setProgress(0);
    setTargetProgress(0);
  };

  if (results) {
    return (
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Comparison Results</h1>
            <p className="text-muted-foreground">
              Comparison ID: {results.comparison_id}
            </p>
          </div>
          <Button onClick={handleReset} variant="outline">
            <RotateCcw className="mr-2 h-4 w-4" />
            New Comparison
          </Button>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Personas Tested</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{results.personas_tested}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Execution Time</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{(results.execution_time_ms / 1000).toFixed(1)}s</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Estimated Cost</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">${results.total_cost_usd.toFixed(2)}</div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Absolute Scores</CardTitle>
            <CardDescription>Mean SSR scores for each concept</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {results.results.absolute_scores
                .sort((a, b) => b.mean_ssr - a.mean_ssr)
                .map((score, idx) => (
                  <div key={score.concept_id} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant={idx === 0 ? "default" : "outline"}>
                          #{idx + 1}
                        </Badge>
                        <span className="font-medium">{score.concept_title}</span>
                      </div>
                      <span className="text-2xl font-bold">
                        {(score.mean_ssr * 100).toFixed(1)}%
                      </span>
                    </div>
                    <Progress value={score.mean_ssr * 100} className="h-2" />
                    <div className="grid grid-cols-4 gap-2 text-sm text-muted-foreground">
                      <div>
                        <div className="font-medium">Definitely Buy</div>
                        <div>{(score.distribution.definitely_buy * 100).toFixed(0)}%</div>
                      </div>
                      <div>
                        <div className="font-medium">Probably Buy</div>
                        <div>{(score.distribution.probably_buy * 100).toFixed(0)}%</div>
                      </div>
                      <div>
                        <div className="font-medium">Maybe</div>
                        <div>{(score.distribution.maybe * 100).toFixed(0)}%</div>
                      </div>
                      <div>
                        <div className="font-medium">Unlikely</div>
                        <div>{(score.distribution.unlikely * 100).toFixed(0)}%</div>
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Statistical Significance</CardTitle>
            <CardDescription>
              Test: {results.results.statistical_significance.test_type === "t_test" ? "t-test" : "ANOVA"}
              {" • "}
              p-value: {results.results.statistical_significance.p_value.toFixed(4)}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Badge variant={results.results.statistical_significance.is_significant ? "default" : "secondary"}>
                  {results.results.statistical_significance.is_significant ? "Significant" : "Not Significant"}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  (α = {results.results.statistical_significance.confidence_level})
                </span>
              </div>
              <p className="text-sm">{results.results.statistical_significance.interpretation}</p>
            </div>
          </CardContent>
        </Card>

        {results.results.segment_analysis.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Segment Analysis</CardTitle>
              <CardDescription>Winners by demographic segments</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {results.results.segment_analysis.map((segment) => (
                  <div key={segment.segment} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium">{segment.segment.replace(/_/g, " ").toUpperCase()}</div>
                        <div className="text-sm text-muted-foreground">
                          {segment.segment_size} personas
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-medium">Winner: {segment.winner}</div>
                        <div className="text-sm text-muted-foreground">
                          {(segment.winner_mean_ssr * 100).toFixed(1)}% vs {(segment.runner_up_mean_ssr * 100).toFixed(1)}%
                        </div>
                      </div>
                    </div>
                    <Separator />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Key Differentiators</CardTitle>
            <CardDescription>AI-extracted insights explaining performance differences</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {results.results.key_differentiators.map((diff, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-primary">•</span>
                  <span className="text-sm">{diff}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Multi-Concept Comparison</h1>
        <p className="text-muted-foreground">
          Compare 2-5 product concepts side-by-side with statistical analysis and segment insights.
        </p>
      </div>

      {isRunning && (
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>Running comparison...</span>
                <span>{progress}%</span>
              </div>
              <Progress value={progress} />
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Comparison Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="personaSetId">Persona Set ID</Label>
              <Input
                id="personaSetId"
                value={personaSetId}
                onChange={(e) => setPersonaSetId(e.target.value)}
                placeholder="default_personas"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="sampleSize">Sample Size (100-10000)</Label>
              <Input
                id="sampleSize"
                type="number"
                min={100}
                max={10000}
                value={sampleSize}
                onChange={(e) => setSampleSize(Number(e.target.value))}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="comparisonMode">Comparison Mode</Label>
            <Select value={comparisonMode} onValueChange={(v: any) => setComparisonMode(v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="rank_based">Rank-Based (Pairwise Preference)</SelectItem>
                <SelectItem value="absolute">Absolute Scores Only</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center space-x-2">
            <Switch id="useMock" checked={useMock} onCheckedChange={setUseMock} />
            <Label htmlFor="useMock">Use Mock Mode (for testing)</Label>
          </div>
        </CardContent>
      </Card>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Concepts ({concepts.length}/5)</h2>
          <Button onClick={addConcept} disabled={concepts.length >= 5} size="sm">
            <Plus className="mr-2 h-4 w-4" />
            Add Concept
          </Button>
        </div>

        {concepts.map((concept, index) => (
          <Card key={concept.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Concept {index + 1}: {concept.id}</CardTitle>
                <Button
                  onClick={() => removeConcept(index)}
                  disabled={concepts.length <= 2}
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
                  <Label>Title</Label>
                  <Input
                    value={concept.title}
                    onChange={(e) => updateConcept(index, "title", e.target.value)}
                    placeholder="e.g., Colgate 3-Day White"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Price</Label>
                  <Input
                    value={concept.price}
                    onChange={(e) => updateConcept(index, "price", e.target.value)}
                    placeholder="e.g., 8,900원 (120g)"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Headline</Label>
                <Input
                  value={concept.headline}
                  onChange={(e) => updateConcept(index, "headline", e.target.value)}
                  placeholder="e.g., 단 3일, 2단계 더 밝은 미소"
                />
              </div>

              <div className="space-y-2">
                <Label>Consumer Insight</Label>
                <Textarea
                  value={concept.consumer_insight}
                  onChange={(e) => updateConcept(index, "consumer_insight", e.target.value)}
                  placeholder="e.g., 커피로 누렇게 변한 치아 때문에 웃기가 꺼려지시나요?"
                  rows={2}
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Key Benefits</Label>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => addListItem(index, "benefits")}
                    disabled={(concept.benefits?.length || 0) >= 5}
                  >
                    <Plus className="h-3 w-3 mr-1" />
                    Add
                  </Button>
                </div>
                <div className="space-y-2">
                  {(concept.benefits || [""]).map((benefit, bIndex) => (
                    <div key={bIndex} className="flex gap-2">
                      <Input
                        value={benefit}
                        onChange={(e) => updateListField(index, "benefits", bIndex, e.target.value)}
                        placeholder={`Benefit ${bIndex + 1}`}
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
                  <Label>Reason to Believe (RTB)</Label>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => addListItem(index, "rtb")}
                    disabled={(concept.rtb?.length || 0) >= 5}
                  >
                    <Plus className="h-3 w-3 mr-1" />
                    Add
                  </Button>
                </div>
                <div className="space-y-2">
                  {(concept.rtb || [""]).map((rtbItem, rIndex) => (
                    <div key={rIndex} className="flex gap-2">
                      <Input
                        value={rtbItem}
                        onChange={(e) => updateListField(index, "rtb", rIndex, e.target.value)}
                        placeholder={`RTB ${rIndex + 1}`}
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
                <Label>Image Prompt</Label>
                <Textarea
                  value={concept.image_prompt}
                  onChange={(e) => updateConcept(index, "image_prompt", e.target.value)}
                  placeholder="e.g., A sleek product on marble counter, soft lighting, high-end photography"
                  rows={2}
                />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="flex justify-end">
        <Button onClick={handleSubmit} disabled={isRunning} size="lg">
          <Play className="mr-2 h-4 w-4" />
          Run Comparison
        </Button>
      </div>
    </div>
  );
}

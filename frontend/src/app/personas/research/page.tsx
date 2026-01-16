"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Loader2, Copy, Check, ArrowRight, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import {
  generateResearchPrompt,
  parseResearchReport,
  saveCorePersona,
  type CorePersona,
} from "@/lib/api";

type Step = "input" | "prompt" | "report" | "review";

export default function ResearchPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("input");
  const [isLoading, setIsLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  // Input state
  const [productCategory, setProductCategory] = useState("");
  const [targetDescription, setTargetDescription] = useState("");
  const [market, setMarket] = useState("korea");

  // Generated prompt
  const [researchPrompt, setResearchPrompt] = useState("");
  const [instructions, setInstructions] = useState("");

  // Parsed persona
  const [report, setReport] = useState("");
  const [parsedPersona, setParsedPersona] = useState<CorePersona | null>(null);
  const [confidence, setConfidence] = useState(0);
  const [warnings, setWarnings] = useState<string[]>([]);

  // Review/Edit state
  const [personaName, setPersonaName] = useState("");
  const [ageRange, setAgeRange] = useState<[number, number]>([30, 45]);
  const [femalePercent, setFemalePercent] = useState(50);
  const [incomeLow, setIncomeLow] = useState(30);
  const [incomeMid, setIncomeMid] = useState(50);
  const [location, setLocation] = useState("urban");
  const [categoryUsage, setCategoryUsage] = useState("medium");
  const [shoppingBehavior, setShoppingBehavior] = useState("smart_shopper");
  const [painPoints, setPainPoints] = useState<string[]>([]);
  const [decisionDrivers, setDecisionDrivers] = useState<string[]>([]);

  const handleGeneratePrompt = async () => {
    if (!productCategory || !targetDescription) {
      toast.error("Please fill in all fields");
      return;
    }

    setIsLoading(true);
    try {
      const result = await generateResearchPrompt(
        { product_category: productCategory, target_description: targetDescription, market },
        true // use mock for demo
      );
      setResearchPrompt(result.research_prompt);
      setInstructions(result.instructions);
      setStep("prompt");
      toast.success("Research prompt generated!");
    } catch (error) {
      toast.error("Failed to generate prompt");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyPrompt = async () => {
    await navigator.clipboard.writeText(researchPrompt);
    setCopied(true);
    toast.success("Copied to clipboard!");
    setTimeout(() => setCopied(false), 2000);
  };

  const handleParseReport = async () => {
    if (report.length < 100) {
      toast.error("Please paste a longer research report");
      return;
    }

    setIsLoading(true);
    try {
      const result = await parseResearchReport({ research_report: report }, true);
      setParsedPersona(result.core_persona);
      setConfidence(result.confidence);
      setWarnings(result.warnings);

      // Populate form with parsed values
      setAgeRange(result.core_persona.age_range);
      setFemalePercent(result.core_persona.gender_distribution.female);
      setIncomeLow(result.core_persona.income_brackets.low);
      setIncomeMid(result.core_persona.income_brackets.mid);
      setLocation(result.core_persona.location);
      setCategoryUsage(result.core_persona.category_usage);
      setShoppingBehavior(result.core_persona.shopping_behavior);
      setPainPoints(result.core_persona.key_pain_points);
      setDecisionDrivers(result.core_persona.decision_drivers);

      setStep("review");
      toast.success("Report parsed successfully!");
    } catch (error) {
      toast.error("Failed to parse report");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSavePersona = async () => {
    if (!personaName) {
      toast.error("Please enter a persona name");
      return;
    }

    setIsLoading(true);
    try {
      const persona: CorePersona & { name: string } = {
        name: personaName,
        age_range: ageRange,
        gender_distribution: { female: femalePercent, male: 100 - femalePercent },
        income_brackets: { low: incomeLow, mid: incomeMid, high: 100 - incomeLow - incomeMid },
        location,
        category_usage: categoryUsage,
        shopping_behavior: shoppingBehavior,
        key_pain_points: painPoints,
        decision_drivers: decisionDrivers,
      };

      const result = await saveCorePersona(persona);
      toast.success(`Persona saved! ID: ${result.id}`);
      router.push(`/concepts/new?persona_id=${result.id}`);
    } catch (error) {
      toast.error("Failed to save persona");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Step 1: Persona Research</h1>
        <p className="text-muted-foreground">
          Define your target audience and extract persona attributes from research.
        </p>
      </div>

      {/* Step indicator */}
      <div className="flex items-center gap-2 mb-6">
        {["input", "prompt", "report", "review"].map((s, i) => (
          <div key={s} className="flex items-center">
            <Badge variant={step === s ? "default" : step > s ? "secondary" : "outline"}>
              {i + 1}. {s.charAt(0).toUpperCase() + s.slice(1)}
            </Badge>
            {i < 3 && <ArrowRight className="w-4 h-4 mx-2 text-muted-foreground" />}
          </div>
        ))}
      </div>

      {/* Step 1: Input */}
      {step === "input" && (
        <Card>
          <CardHeader>
            <CardTitle>Describe Your Target Audience</CardTitle>
            <CardDescription>
              Tell us about your product and target customers
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="category">Product Category</Label>
              <Input
                id="category"
                placeholder="e.g., oral care, skincare, beverages"
                value={productCategory}
                onChange={(e) => setProductCategory(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="target">Target Audience Description</Label>
              <Textarea
                id="target"
                placeholder="e.g., 30-40대 직장인 여성, 커피 자주 마심, 미백 관심 많음"
                rows={3}
                value={targetDescription}
                onChange={(e) => setTargetDescription(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="market">Market</Label>
              <select
                id="market"
                className="w-full p-2 border rounded-md"
                value={market}
                onChange={(e) => setMarket(e.target.value)}
              >
                <option value="korea">Korea</option>
                <option value="us">United States</option>
                <option value="global">Global</option>
              </select>
            </div>

            <Button onClick={handleGeneratePrompt} disabled={isLoading} className="w-full">
              {isLoading ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Generating...</>
              ) : (
                "Generate Research Prompt"
              )}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Generated Prompt */}
      {step === "prompt" && (
        <Card>
          <CardHeader>
            <CardTitle>Research Prompt Generated</CardTitle>
            <CardDescription>{instructions}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="relative">
              <pre className="p-4 bg-muted rounded-lg text-sm whitespace-pre-wrap max-h-96 overflow-y-auto">
                {researchPrompt}
              </pre>
              <Button
                variant="outline"
                size="sm"
                className="absolute top-2 right-2"
                onClick={handleCopyPrompt}
              >
                {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>

            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setStep("input")}>
                Back
              </Button>
              <Button onClick={() => setStep("report")} className="flex-1">
                I have the report <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 3: Paste Report */}
      {step === "report" && (
        <Card>
          <CardHeader>
            <CardTitle>Paste Research Report</CardTitle>
            <CardDescription>
              Paste the Gemini Deep Research report here
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              placeholder="Paste your research report here..."
              rows={12}
              value={report}
              onChange={(e) => setReport(e.target.value)}
            />
            <p className="text-sm text-muted-foreground">
              {report.length} characters ({report.length < 100 ? "need at least 100" : "ready"})
            </p>

            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setStep("prompt")}>
                Back
              </Button>
              <Button
                onClick={handleParseReport}
                disabled={isLoading || report.length < 100}
                className="flex-1"
              >
                {isLoading ? (
                  <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Parsing...</>
                ) : (
                  "Extract Persona"
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 4: Review & Edit */}
      {step === "review" && parsedPersona && (
        <div className="space-y-6">
          {/* Confidence & Warnings */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-sm text-muted-foreground">Extraction Confidence</span>
                  <p className="text-2xl font-bold">{(confidence * 100).toFixed(0)}%</p>
                </div>
                {warnings.length > 0 && (
                  <div className="flex items-start gap-2">
                    <AlertCircle className="h-5 w-5 text-yellow-500" />
                    <div className="text-sm">
                      {warnings.map((w, i) => (
                        <p key={i} className="text-muted-foreground">{w}</p>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Edit Form */}
          <Card>
            <CardHeader>
              <CardTitle>Review & Edit Persona</CardTitle>
              <CardDescription>
                Verify and adjust the extracted persona attributes
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label>Persona Name</Label>
                <Input
                  placeholder="e.g., Coffee-loving Professional Women"
                  value={personaName}
                  onChange={(e) => setPersonaName(e.target.value)}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Age Range: {ageRange[0]} - {ageRange[1]}</Label>
                  <div className="flex gap-2">
                    <Input
                      type="number"
                      min={15}
                      max={80}
                      value={ageRange[0]}
                      onChange={(e) => setAgeRange([parseInt(e.target.value), ageRange[1]])}
                    />
                    <Input
                      type="number"
                      min={15}
                      max={80}
                      value={ageRange[1]}
                      onChange={(e) => setAgeRange([ageRange[0], parseInt(e.target.value)])}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Gender: {femalePercent}% Female / {100 - femalePercent}% Male</Label>
                  <Slider
                    value={[femalePercent]}
                    min={0}
                    max={100}
                    step={5}
                    onValueChange={(v) => setFemalePercent(v[0])}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Income Distribution (must sum to 100%)</Label>
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <span className="text-xs">Low: {incomeLow}%</span>
                    <Slider
                      value={[incomeLow]}
                      min={0}
                      max={100}
                      step={5}
                      onValueChange={(v) => setIncomeLow(v[0])}
                    />
                  </div>
                  <div>
                    <span className="text-xs">Mid: {incomeMid}%</span>
                    <Slider
                      value={[incomeMid]}
                      min={0}
                      max={100}
                      step={5}
                      onValueChange={(v) => setIncomeMid(v[0])}
                    />
                  </div>
                  <div>
                    <span className="text-xs">High: {100 - incomeLow - incomeMid}%</span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Location</Label>
                  <select
                    className="w-full p-2 border rounded-md"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                  >
                    <option value="urban">Urban</option>
                    <option value="suburban">Suburban</option>
                    <option value="rural">Rural</option>
                    <option value="mixed">Mixed</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label>Category Usage</Label>
                  <select
                    className="w-full p-2 border rounded-md"
                    value={categoryUsage}
                    onChange={(e) => setCategoryUsage(e.target.value)}
                  >
                    <option value="high">High (daily)</option>
                    <option value="medium">Medium (weekly)</option>
                    <option value="low">Low (monthly)</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label>Shopping Behavior</Label>
                  <select
                    className="w-full p-2 border rounded-md"
                    value={shoppingBehavior}
                    onChange={(e) => setShoppingBehavior(e.target.value)}
                  >
                    <option value="impulsive">Impulsive</option>
                    <option value="budget">Budget-conscious</option>
                    <option value="quality">Quality-focused</option>
                    <option value="smart_shopper">Smart Shopper</option>
                  </select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Key Pain Points (comma-separated)</Label>
                <Input
                  value={painPoints.join(", ")}
                  onChange={(e) => setPainPoints(e.target.value.split(",").map((s) => s.trim()).filter(Boolean))}
                />
              </div>

              <div className="space-y-2">
                <Label>Decision Drivers (comma-separated)</Label>
                <Input
                  value={decisionDrivers.join(", ")}
                  onChange={(e) => setDecisionDrivers(e.target.value.split(",").map((s) => s.trim()).filter(Boolean))}
                />
              </div>

              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setStep("report")}>
                  Back
                </Button>
                <Button onClick={handleSavePersona} disabled={isLoading} className="flex-1">
                  {isLoading ? (
                    <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Saving...</>
                  ) : (
                    <>Save & Continue to Concept Builder <ArrowRight className="ml-2 h-4 w-4" /></>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

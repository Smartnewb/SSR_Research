"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
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
  Loader2,
  Users,
  BarChart3,
  Download,
  Play,
  Eye,
  CheckCircle,
  RefreshCw,
} from "lucide-react";
import { toast } from "sonner";
import {
  generatePersonas,
  previewPersonas,
  getCorePersona,
  getConcept,
  type GeneratedPersona,
  type GeneratePersonasResponse,
  type CorePersonaResponse,
  type ConceptResponse,
  type BundledExport,
} from "@/lib/api";

function GenerateContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const personaId = searchParams.get("persona_id");
  const conceptId = searchParams.get("concept_id");

  const [sampleSize, setSampleSize] = useState(100);
  const [randomSeed, setRandomSeed] = useState<number | undefined>(undefined);
  const [useFixedSeed, setUseFixedSeed] = useState(false);

  const [isGenerating, setIsGenerating] = useState(false);
  const [isPreviewing, setIsPreviewing] = useState(false);

  const [previewData, setPreviewData] = useState<GeneratedPersona[]>([]);
  const [generationResult, setGenerationResult] = useState<GeneratePersonasResponse | null>(null);

  const [corePersonaData, setCorePersonaData] = useState<CorePersonaResponse | null>(null);
  const [conceptData, setConceptData] = useState<ConceptResponse | null>(null);

  const [activeTab, setActiveTab] = useState("preview");

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
      const result = await generatePersonas({
        core_persona_id: personaId || undefined,
        sample_size: sampleSize,
        random_seed: useFixedSeed ? randomSeed : undefined,
      });
      setGenerationResult(result);
      setActiveTab("results");
      toast.success(`Generated ${result.total_personas} personas!`);
    } catch (error) {
      toast.error("Failed to generate personas");
      console.error(error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownload = () => {
    if (!generationResult) return;

    const bundledExport: BundledExport = {
      export_version: "1.0",
      exported_at: new Date().toISOString(),
      core_persona: corePersonaData,
      concept: conceptData,
      generation: generationResult,
    };

    const dataStr = JSON.stringify(bundledExport, null, 2);
    const blob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `survey_bundle_${generationResult.job_id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success("Downloaded bundled JSON (persona + concept + generated personas)");
  };

  const handleRunSurvey = () => {
    if (!generationResult) return;
    // Store generation result in localStorage for survey page
    localStorage.setItem("generated_personas", JSON.stringify(generationResult));
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
            <div className="space-y-3">
              <Label>Sample Size: {sampleSize.toLocaleString()}</Label>
              <Slider
                value={[sampleSize]}
                min={5}
                max={1000}
                step={5}
                onValueChange={(v) => setSampleSize(v[0])}
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>5 (Quick test)</span>
                <span>1,000 (Full study)</span>
              </div>
            </div>

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
              <TabsTrigger value="results" disabled={!generationResult}>
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
              {generationResult && (
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

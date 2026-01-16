"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Loader2,
  Sparkles,
  Check,
  AlertCircle,
  ArrowRight,
  Eye,
} from "lucide-react";
import { toast } from "sonner";
import {
  assistConceptField,
  validateConcept,
  saveConcept,
  type ProductConcept,
  type Suggestion,
  type ConceptValidateResponse,
} from "@/lib/api";

interface FieldConfig {
  key: keyof ProductConcept;
  label: string;
  placeholder: string;
  description: string;
  multiline: boolean;
}

const CONCEPT_FIELDS: FieldConfig[] = [
  {
    key: "title",
    label: "Product Title",
    placeholder: "e.g., WhiteBright Pro Toothpaste",
    description: "The name of your product concept",
    multiline: false,
  },
  {
    key: "headline",
    label: "Headline",
    placeholder: "e.g., Professional whitening in just 7 days",
    description: "The main attention-grabbing statement",
    multiline: false,
  },
  {
    key: "consumer_insight",
    label: "Consumer Insight",
    placeholder: "e.g., Coffee lovers struggle with teeth staining but don't want to give up their daily cup",
    description: "The key consumer truth your product addresses",
    multiline: true,
  },
  {
    key: "benefit",
    label: "Key Benefit",
    placeholder: "e.g., Removes coffee and tea stains without sensitivity",
    description: "The primary benefit consumers will experience",
    multiline: true,
  },
  {
    key: "rtb",
    label: "Reason to Believe (RTB)",
    placeholder: "e.g., Contains patented ActiveWhite technology clinically proven to be 3x more effective",
    description: "Why consumers should believe your benefit claim",
    multiline: true,
  },
  {
    key: "image_description",
    label: "Visual Description",
    placeholder: "e.g., Sleek white tube with blue accents, before/after smile comparison",
    description: "How the product concept would be visually presented",
    multiline: true,
  },
  {
    key: "price",
    label: "Price Point",
    placeholder: "e.g., $12.99 (Premium segment)",
    description: "Target price and positioning",
    multiline: false,
  },
];

function ConceptBuilderContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const personaId = searchParams.get("persona_id");

  const [isLoading, setIsLoading] = useState(false);
  const [concept, setConcept] = useState<ProductConcept>({
    title: "",
    headline: "",
    consumer_insight: "",
    benefit: "",
    rtb: "",
    image_description: "",
    price: "",
  });

  // AI Assistant modal state
  const [assistModalOpen, setAssistModalOpen] = useState(false);
  const [currentField, setCurrentField] = useState<keyof ProductConcept | null>(null);
  const [roughIdea, setRoughIdea] = useState("");
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [isAssisting, setIsAssisting] = useState(false);

  // Validation state
  const [validation, setValidation] = useState<ConceptValidateResponse | null>(null);
  const [isValidating, setIsValidating] = useState(false);

  const handleFieldChange = (key: keyof ProductConcept, value: string) => {
    setConcept((prev) => ({ ...prev, [key]: value }));
    setValidation(null); // Reset validation when content changes
  };

  const openAssistModal = (field: keyof ProductConcept) => {
    setCurrentField(field);
    setRoughIdea(concept[field]);
    setSuggestions([]);
    setAssistModalOpen(true);
  };

  const handleAssist = async () => {
    if (!currentField || !roughIdea.trim()) {
      toast.error("Please enter your rough idea first");
      return;
    }

    setIsAssisting(true);
    try {
      const context: Record<string, string> = {};
      Object.entries(concept).forEach(([k, v]) => {
        if (v && k !== currentField) {
          context[k] = v;
        }
      });

      const result = await assistConceptField(
        {
          field: currentField,
          rough_idea: roughIdea,
          context: Object.keys(context).length > 0 ? context : undefined,
        },
        true // use mock
      );
      setSuggestions(result.suggestions);
    } catch (error) {
      toast.error("Failed to get AI suggestions");
      console.error(error);
    } finally {
      setIsAssisting(false);
    }
  };

  const applySuggestion = (text: string) => {
    if (currentField) {
      handleFieldChange(currentField, text);
      setAssistModalOpen(false);
      toast.success("Suggestion applied!");
    }
  };

  const handleValidate = async () => {
    const emptyFields = CONCEPT_FIELDS.filter((f) => !concept[f.key].trim());
    if (emptyFields.length > 0) {
      toast.error(`Please fill in all fields: ${emptyFields.map((f) => f.label).join(", ")}`);
      return;
    }

    setIsValidating(true);
    try {
      const result = await validateConcept(concept, true);
      setValidation(result);
      if (result.is_valid) {
        toast.success(`Concept validated! Score: ${result.score}/100`);
      } else {
        toast.warning(`Validation score: ${result.score}/100. See suggestions below.`);
      }
    } catch (error) {
      toast.error("Failed to validate concept");
      console.error(error);
    } finally {
      setIsValidating(false);
    }
  };

  const handleSave = async () => {
    if (!validation?.is_valid) {
      toast.error("Please validate your concept first");
      return;
    }

    setIsLoading(true);
    try {
      const result = await saveConcept(
        { ...concept, persona_id: personaId || undefined },
        true
      );
      toast.success(`Concept saved! ID: ${result.id}`);
      router.push(`/personas/generate?concept_id=${result.id}${personaId ? `&persona_id=${personaId}` : ""}`);
    } catch (error) {
      toast.error("Failed to save concept");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const getFieldStatus = (key: keyof ProductConcept) => {
    if (!validation) return null;
    return validation.feedback[key];
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Step 2: Concept Builder</h1>
        <p className="text-muted-foreground">
          Build your product concept card with AI assistance.
          {personaId && (
            <Badge variant="outline" className="ml-2">
              Persona: {personaId}
            </Badge>
          )}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Form */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Concept Fields</CardTitle>
              <CardDescription>
                Fill in all 7 fields. Use the AI assistant for help.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {CONCEPT_FIELDS.map((field) => {
                const status = getFieldStatus(field.key);
                return (
                  <div key={field.key} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label htmlFor={field.key} className="flex items-center gap-2">
                        {field.label}
                        {status && (
                          <Badge
                            variant={status.status === "good" ? "default" : "destructive"}
                            className="text-xs"
                          >
                            {status.status}
                          </Badge>
                        )}
                      </Label>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openAssistModal(field.key)}
                      >
                        <Sparkles className="h-4 w-4 mr-1" />
                        AI Assist
                      </Button>
                    </div>
                    {field.multiline ? (
                      <Textarea
                        id={field.key}
                        placeholder={field.placeholder}
                        value={concept[field.key]}
                        onChange={(e) => handleFieldChange(field.key, e.target.value)}
                        rows={3}
                        className={status?.status === "needs_work" ? "border-yellow-500" : ""}
                      />
                    ) : (
                      <Input
                        id={field.key}
                        placeholder={field.placeholder}
                        value={concept[field.key]}
                        onChange={(e) => handleFieldChange(field.key, e.target.value)}
                        className={status?.status === "needs_work" ? "border-yellow-500" : ""}
                      />
                    )}
                    {status?.message && status.status === "needs_work" && (
                      <p className="text-xs text-yellow-600">{status.message}</p>
                    )}
                    <p className="text-xs text-muted-foreground">{field.description}</p>
                  </div>
                );
              })}

              <div className="flex gap-2 pt-4">
                <Button
                  variant="outline"
                  onClick={handleValidate}
                  disabled={isValidating}
                  className="flex-1"
                >
                  {isValidating ? (
                    <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Validating...</>
                  ) : (
                    <><Check className="mr-2 h-4 w-4" /> Validate Concept</>
                  )}
                </Button>
                <Button
                  onClick={handleSave}
                  disabled={isLoading || !validation?.is_valid}
                  className="flex-1"
                >
                  {isLoading ? (
                    <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Saving...</>
                  ) : (
                    <>Save & Continue <ArrowRight className="ml-2 h-4 w-4" /></>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Validation Results */}
          {validation && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  {validation.is_valid ? (
                    <Check className="h-5 w-5 text-green-500" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-yellow-500" />
                  )}
                  Validation Results
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-4 mb-4">
                  <div className="text-3xl font-bold">{validation.score}/100</div>
                  <Badge variant={validation.is_valid ? "default" : "secondary"}>
                    {validation.is_valid ? "Ready" : "Needs Work"}
                  </Badge>
                </div>
                {validation.suggestions.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-sm font-medium">Suggestions:</p>
                    <ul className="text-sm text-muted-foreground space-y-1">
                      {validation.suggestions.map((s, i) => (
                        <li key={i}>• {s}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right: Live Preview */}
        <div className="lg:sticky lg:top-4">
          <Card className="h-fit">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Eye className="h-5 w-5" />
                Live Preview
              </CardTitle>
              <CardDescription>
                This is how your concept card will appear in surveys
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="border rounded-lg p-6 bg-gradient-to-b from-white to-gray-50">
                {/* Product Title */}
                <h2 className="text-2xl font-bold text-center mb-2">
                  {concept.title || "Product Title"}
                </h2>

                {/* Headline */}
                <p className="text-lg text-center text-blue-600 font-medium mb-6">
                  {concept.headline || "Your headline here"}
                </p>

                {/* Visual placeholder */}
                <div className="bg-gray-100 rounded-lg p-4 mb-6 min-h-[100px] flex items-center justify-center">
                  <p className="text-sm text-gray-500 text-center italic">
                    {concept.image_description || "[Visual description will appear here]"}
                  </p>
                </div>

                {/* Consumer Insight */}
                {concept.consumer_insight && (
                  <div className="mb-4">
                    <p className="text-sm text-gray-600 italic">
                      "{concept.consumer_insight}"
                    </p>
                  </div>
                )}

                {/* Benefit */}
                <div className="mb-4">
                  <h3 className="font-semibold text-sm uppercase text-gray-500 mb-1">
                    Key Benefit
                  </h3>
                  <p className="text-gray-800">
                    {concept.benefit || "Your key benefit statement"}
                  </p>
                </div>

                {/* RTB */}
                <div className="mb-4">
                  <h3 className="font-semibold text-sm uppercase text-gray-500 mb-1">
                    Why It Works
                  </h3>
                  <p className="text-gray-700 text-sm">
                    {concept.rtb || "Your reason to believe"}
                  </p>
                </div>

                {/* Price */}
                <div className="text-center pt-4 border-t">
                  <span className="text-2xl font-bold text-green-600">
                    {concept.price || "$X.XX"}
                  </span>
                </div>
              </div>

              {/* Field completion indicator */}
              <div className="mt-4 flex flex-wrap gap-2">
                {CONCEPT_FIELDS.map((field) => (
                  <Badge
                    key={field.key}
                    variant={concept[field.key].trim() ? "default" : "outline"}
                    className="text-xs"
                  >
                    {field.label}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* AI Assistant Modal */}
      <Dialog open={assistModalOpen} onOpenChange={setAssistModalOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5" />
              AI Writing Assistant
            </DialogTitle>
            <DialogDescription>
              {currentField && CONCEPT_FIELDS.find((f) => f.key === currentField)?.description}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Your rough idea or draft</Label>
              <Textarea
                placeholder="Enter your rough idea, key points, or draft text..."
                value={roughIdea}
                onChange={(e) => setRoughIdea(e.target.value)}
                rows={3}
              />
            </div>

            <Button onClick={handleAssist} disabled={isAssisting} className="w-full">
              {isAssisting ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Generating suggestions...</>
              ) : (
                <><Sparkles className="mr-2 h-4 w-4" /> Get AI Suggestions</>
              )}
            </Button>

            {suggestions.length > 0 && (
              <div className="space-y-3">
                <Label>Suggestions (click to apply)</Label>
                {suggestions.map((suggestion, index) => (
                  <Card
                    key={index}
                    className="cursor-pointer hover:border-blue-500 transition-colors"
                    onClick={() => applySuggestion(suggestion.text)}
                  >
                    <CardContent className="pt-4">
                      <p className="font-medium mb-2">{suggestion.text}</p>
                      <p className="text-sm text-muted-foreground italic">
                        {suggestion.rationale}
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default function ConceptBuilderPage() {
  return (
    <Suspense fallback={<div className="flex justify-center py-8"><Loader2 className="h-8 w-8 animate-spin" /></div>}>
      <ConceptBuilderContent />
    </Suspense>
  );
}

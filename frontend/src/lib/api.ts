import axios from "axios";
import type {
  SurveyRequest,
  SurveyResponse,
  ABTestRequest,
  ABTestResponse,
  HealthResponse,
  Archetype,
  SegmentMarketRequest,
  SegmentMarketResponse,
  ArchetypeGenerateRequest,
  ArchetypeGenerateResponse,
  DistributionPlanItem,
  GeneratedPersona,
} from "./types";

export type { GeneratedPersona } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export async function checkHealth(): Promise<HealthResponse> {
  const response = await api.get<HealthResponse>("/health");
  return response.data;
}

export async function runSurvey(request: SurveyRequest): Promise<SurveyResponse> {
  const response = await api.post<SurveyResponse>("/api/surveys", request);
  return response.data;
}

export async function runABTest(request: ABTestRequest): Promise<ABTestResponse> {
  const response = await api.post<ABTestResponse>("/api/surveys/compare", request);
  return response.data;
}

export function createWebSocket(surveyId: string): WebSocket {
  const wsUrl = API_BASE_URL.replace("http", "ws");
  return new WebSocket(`${wsUrl}/ws/surveys/${surveyId}`);
}

export function formatCost(cost: number): string {
  return `$${cost.toFixed(4)}`;
}

export function formatScore(score: number): string {
  return (score * 100).toFixed(1) + "%";
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
}

export function getScoreColor(score: number): string {
  if (score >= 0.7) return "text-green-600";
  if (score >= 0.5) return "text-yellow-600";
  return "text-red-600";
}

export function getScoreBgColor(score: number): string {
  if (score >= 0.7) return "bg-green-100";
  if (score >= 0.5) return "bg-yellow-100";
  return "bg-red-100";
}

// Research API
export interface ResearchPromptRequest {
  product_category: string;
  target_description: string;
  market?: string;
}

export interface ResearchPromptResponse {
  research_prompt: string;
  instructions: string;
}

export async function generateResearchPrompt(
  request: ResearchPromptRequest,
  useMock = false
): Promise<ResearchPromptResponse> {
  const response = await api.post<ResearchPromptResponse>(
    `/api/research/generate-prompt?use_mock=${useMock}`,
    request
  );
  return response.data;
}

export interface ParseReportRequest {
  research_report: string;
}

export interface CorePersona {
  age_range: [number, number];
  gender_distribution: { female: number; male: number };
  income_brackets: { low: number; mid: number; high: number };
  location: string;
  category_usage: string;
  shopping_behavior: string;
  key_pain_points: string[];
  decision_drivers: string[];
}

export interface ParseReportResponse {
  core_persona: CorePersona;
  confidence: number;
  warnings: string[];
}

export async function parseResearchReport(
  request: ParseReportRequest,
  useMock = false
): Promise<ParseReportResponse> {
  const response = await api.post<ParseReportResponse>(
    `/api/research/parse-report?use_mock=${useMock}`,
    request
  );
  return response.data;
}

export interface SaveCorePersonaRequest extends CorePersona {
  name: string;
}

export interface SaveCorePersonaResponse {
  id: string;
  created_at: string;
  status: string;
}

export async function saveCorePersona(
  request: SaveCorePersonaRequest
): Promise<SaveCorePersonaResponse> {
  const response = await api.post<SaveCorePersonaResponse>(
    "/api/personas/core",
    request
  );
  return response.data;
}

// Concept API
export interface ConceptAssistRequest {
  field: string;
  rough_idea: string;
  context?: Record<string, string>;
}

export interface Suggestion {
  text: string;
  rationale: string;
}

export interface ConceptAssistResponse {
  suggestions: Suggestion[];
}

export async function assistConceptField(
  request: ConceptAssistRequest,
  useMock = false
): Promise<ConceptAssistResponse> {
  const response = await api.post<ConceptAssistResponse>(
    `/api/concepts/assist?use_mock=${useMock}`,
    request
  );
  return response.data;
}

export interface ProductConcept {
  title: string;
  headline: string;
  consumer_insight: string;
  benefit: string;
  rtb: string;
  image_description: string;
  price: string;
}

export interface ConceptValidateResponse {
  is_valid: boolean;
  score: number;
  feedback: Record<string, { status: string; message: string }>;
  suggestions: string[];
}

export async function validateConcept(
  concept: ProductConcept,
  useMock = false
): Promise<ConceptValidateResponse> {
  const response = await api.post<ConceptValidateResponse>(
    `/api/concepts/validate?use_mock=${useMock}`,
    concept
  );
  return response.data;
}

export interface SaveConceptRequest extends ProductConcept {
  persona_id?: string;
}

export interface SaveConceptResponse {
  id: string;
  validation_score: number;
  created_at: string;
}

export async function saveConcept(
  request: SaveConceptRequest,
  useMock = false
): Promise<SaveConceptResponse> {
  const response = await api.post<SaveConceptResponse>(
    `/api/concepts?use_mock=${useMock}`,
    request
  );
  return response.data;
}

// Persona Generation API
export interface GeneratePersonasRequest {
  core_persona_id?: string;
  core_config?: CorePersona;
  sample_size: number;
  random_seed?: number;
}

// GeneratedPersona is imported from types.ts via the import statement at the top
// (using the re-export below for backwards compatibility)

export interface GeneratePersonasResponse {
  job_id: string;
  total_personas: number;
  distribution_stats: {
    age?: { mean: number; std: number; min: number; max: number };
    gender?: Record<string, number>;
    income?: Record<string, number>;
  };
  personas: GeneratedPersona[];
}

export async function generatePersonas(
  request: GeneratePersonasRequest
): Promise<GeneratePersonasResponse> {
  const response = await api.post<GeneratePersonasResponse>(
    "/api/personas/generate",
    request
  );
  return response.data;
}

export interface PreviewPersonasResponse {
  preview_personas: GeneratedPersona[];
}

export async function previewPersonas(
  corePersonaId?: string,
  count = 5
): Promise<PreviewPersonasResponse> {
  const params = new URLSearchParams();
  if (corePersonaId) params.append("core_persona_id", corePersonaId);
  params.append("count", count.toString());

  const response = await api.get<PreviewPersonasResponse>(
    `/api/personas/preview?${params.toString()}`
  );
  return response.data;
}

export interface CorePersonaResponse extends CorePersona {
  id: string;
  name: string;
  created_at: string;
}

export async function getCorePersona(id: string): Promise<CorePersonaResponse | null> {
  try {
    const response = await api.get<CorePersonaResponse>(`/api/personas/core/${id}`);
    return response.data;
  } catch {
    return null;
  }
}

export interface ConceptResponse extends ProductConcept {
  id: string;
  validation_score: number;
  created_at: string;
}

export async function getConcept(id: string): Promise<ConceptResponse | null> {
  try {
    const response = await api.get<ConceptResponse>(`/api/concepts/${id}`);
    return response.data;
  } catch {
    return null;
  }
}

export interface BundledExport {
  export_version: string;
  exported_at: string;
  core_persona?: CorePersonaResponse | null;
  concept?: ConceptResponse | null;
  generation: GeneratePersonasResponse;
}

// =============================================================================
// Multi-Archetype Stratified Sampling API (v2.0)
// =============================================================================

export async function segmentMarket(
  request: SegmentMarketRequest
): Promise<SegmentMarketResponse> {
  const response = await api.post<SegmentMarketResponse>(
    "/api/archetypes/segment",
    request
  );
  return response.data;
}

export interface DistributePreviewRequest {
  archetypes: Archetype[];
  total_samples: number;
}

export interface DistributePreviewResponse {
  total_samples: number;
  distribution_plan: DistributionPlanItem[];
  segment_count: number;
}

export async function previewDistribution(
  archetypes: Archetype[],
  totalSamples: number
): Promise<DistributePreviewResponse> {
  const response = await api.post<DistributePreviewResponse>(
    `/api/archetypes/distribute?total_samples=${totalSamples}`,
    archetypes
  );
  return response.data;
}

export async function generateFromArchetypes(
  request: ArchetypeGenerateRequest
): Promise<ArchetypeGenerateResponse> {
  const response = await api.post<ArchetypeGenerateResponse>(
    "/api/archetypes/generate",
    request
  );
  return response.data;
}

export interface FullPipelineRequest {
  research_report: string;
  product_category?: string;
  total_samples: number;
  enrich: boolean;
  currency: "KRW" | "USD";
}

export interface FullPipelineResponse {
  pipeline_status: string;
  segmentation: {
    archetypes: Archetype[];
    segment_count: number;
    warnings: string[];
  };
  generation: {
    total_count: number;
    distribution_plan: DistributionPlanItem[];
    segment_stats: Record<string, { count: number; segment_name: string }>;
    enriched: boolean;
  };
  personas: Array<{
    id: string;
    segment_id?: string;
    segment_name?: string;
    age: number;
    gender: string;
    income_bracket: string;
    income_value: number;
    currency: string;
    location: string;
    category_usage: string;
    shopping_behavior: string;
    core_traits: string[];
    pain_points: string[];
    decision_drivers: string[];
    bio?: string;
    enriched: boolean;
  }>;
}

export async function runFullArchetypePipeline(
  request: FullPipelineRequest
): Promise<FullPipelineResponse> {
  const response = await api.post<FullPipelineResponse>(
    `/api/archetypes/full-pipeline?total_samples=${request.total_samples}&enrich=${request.enrich}&currency=${request.currency}`,
    request.research_report,
    {
      headers: {
        "Content-Type": "text/plain",
      },
      params: {
        product_category: request.product_category,
      },
    }
  );
  return response.data;
}

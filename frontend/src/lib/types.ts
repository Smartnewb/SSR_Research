import type { ReportData } from "./report/types";

export interface DemographicsFilter {
  age_range?: [number, number];
  gender?: string[];
  income_bracket?: string[];
  occupation?: string[];
  location?: string[];
}

export interface SurveyRequest {
  product_description: string;
  sample_size: number;
  demographics?: DemographicsFilter;
  use_mock: boolean;
  model: string;
}

export interface ABTestRequest {
  product_a: string;
  product_b: string;
  product_a_name: string;
  product_b_name: string;
  sample_size: number;
  demographics?: DemographicsFilter;
  use_mock: boolean;
  model: string;
}

export interface SurveyResultItem {
  persona_id: string;
  ssr_score: number;
  likert_5: number;
  scale_10: number;
  response_text: string;
  persona_data?: Record<string, unknown>;
  tokens_used: number;
  cost: number;
  latency_ms: number;
}

export interface SurveyResponse {
  survey_id: string;
  product_description: string;
  sample_size: number;
  mean_score: number;
  median_score: number;
  std_dev: number;
  min_score: number;
  max_score: number;
  score_distribution: Record<string, number>;
  total_cost: number;
  total_tokens: number;
  execution_time_seconds: number;
  results: SurveyResultItem[];
  created_at: string;
}

export interface ABTestStatistics {
  mean_difference: number;
  relative_difference: number;
  t_statistic: number;
  p_value: number;
  confidence_interval: [number, number];
  effect_size: number;
  significant: boolean;
  winner: string | null;
}

export interface ABTestResponse {
  test_id: string;
  product_a_name: string;
  product_b_name: string;
  results_a: SurveyResponse;
  results_b: SurveyResponse;
  statistics: ABTestStatistics;
  created_at: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
}

export type SurveyStatus = "idle" | "running" | "completed" | "error";

export interface WebSocketProgress {
  type: "progress" | "result" | "error";
  survey_id: string;
  status?: string;
  progress?: number;
  current_persona?: number;
  total_personas?: number;
  message?: string;
  data?: SurveyResponse;
  error?: string;
}

// Multi-concept comparison types (Concept Board format)
// Follows standard marketing research concept testing structure
export interface ConceptInput {
  id: string;
  title: string;           // Product name
  headline: string;        // Eye-catching one-liner
  consumer_insight: string; // Consumer pain point (empathy)
  benefits: string[];      // 3-5 value propositions
  rtb: string[];           // Reasons to Believe (technical proof)
  image_prompt: string;    // DALL-E style image description
  price: string;           // Price with unit
}

export interface MultiCompareRequest {
  concepts: ConceptInput[];
  persona_set_id: string;
  sample_size: number;
  comparison_mode: "rank_based" | "absolute";
  use_mock: boolean;
}

export interface DistributionStats {
  definitely_buy: number;
  probably_buy: number;
  maybe: number;
  unlikely: number;
}

export interface AbsoluteScore {
  concept_id: string;
  concept_title: string;
  mean_ssr: number;
  std_dev: number;
  median_ssr: number;
  distribution: DistributionStats;
}

export interface PreferenceMatrixEntry {
  concept_a: string;
  concept_b: string;
  preference_rate: number;
}

export interface RelativePreference {
  winner: string;
  preference_matrix: PreferenceMatrixEntry[];
}

export interface StatisticalSignificance {
  test_type: "t_test" | "anova";
  statistic: number;
  p_value: number;
  is_significant: boolean;
  confidence_level: number;
  interpretation: string;
}

export interface SegmentAnalysis {
  segment: string;
  segment_size: number;
  winner: string;
  winner_mean_ssr: number;
  runner_up: string;
  runner_up_mean_ssr: number;
  mean_diff: number;
}

export interface ComparisonResults {
  absolute_scores: AbsoluteScore[];
  relative_preference?: RelativePreference;
  statistical_significance: StatisticalSignificance;
  segment_analysis: SegmentAnalysis[];
  key_differentiators: string[];
}

export interface MultiCompareResponse {
  comparison_id: string;
  results: ComparisonResults;
  execution_time_ms: number;
  total_cost_usd: number;
  personas_tested: number;
}

// =============================================================================
// Multi-Archetype Stratified Sampling Pipeline (v2.0)
// =============================================================================

export interface GenderDistribution {
  female: number;
  male: number;
}

export interface ArchetypeDemographics {
  age_range: [number, number];
  gender_distribution: GenderDistribution;
}

export interface Archetype {
  segment_id?: string;
  segment_name: string;
  share_ratio: number;
  demographics: ArchetypeDemographics;
  income_level: "none" | "low" | "mid" | "high";
  category_usage: "high" | "medium" | "low";
  shopping_behavior: string;
  core_traits: string[];
  pain_points: string[];
  decision_drivers: string[];
}

export interface SegmentMarketRequest {
  research_report: string;
  product_category?: string;
  target_segments?: number;
}

export interface SegmentMarketResponse {
  archetypes: Archetype[];
  total_share: number;
  segment_count: number;
  warnings: string[];
}

export interface ArchetypeGenerateRequest {
  archetypes: Archetype[];
  total_samples: number;
  product_context?: string;
  currency: "KRW" | "USD";
  enrich: boolean;
  random_seed?: number;
}

export interface DistributionPlanItem {
  segment_id: string;
  segment_name: string;
  count: number;
  share_ratio: number;
  actual_ratio: number;
}

export interface GeneratedPersona {
  id: string;
  segment_id?: string;
  segment_name?: string;
  age: number;
  gender: string;
  income_bracket: string;
  income_value: number;
  currency?: string;
  location: string;
  category_usage: string;
  shopping_behavior: string;
  core_traits?: string[];
  pain_points: string[];
  decision_drivers: string[];
  bio?: string;
  enriched?: boolean;
  system_prompt?: string;
}

export interface PersonaDistributionStats {
  age: { mean: number; std: number; min: number; max: number };
  gender: Record<string, number>;
  income: Record<string, number>;
}

export interface ArchetypeGenerateResponse {
  personas: GeneratedPersona[];
  distribution_plan: DistributionPlanItem[];
  stats: PersonaDistributionStats;
  segment_stats: Record<string, { count: number; segment_name: string }>;
  total_count: number;
  enriched: boolean;
}

// Sample size presets with cost/time estimates
export type SampleSizeScale = "debug" | "pilot" | "standard" | "massive";

export interface SampleSizeOption {
  value: number;
  scale: SampleSizeScale;
  cost: string;
  time: string;
  description: string;
}

// =============================================================================
// QIE (Qualitative Insight Engine) v2.0 - Two-Tier Map-Reduce
// =============================================================================

export type QIEJobStatus =
  | "pending"
  | "tier1_processing"
  | "aggregating"
  | "tier2_synthesis"
  | "completed"
  | "failed";

export type SentimentCategory =
  | "Price"
  | "UX"
  | "Trust"
  | "Feature"
  | "Convenience"
  | "Other";

export type KanoCategory =
  | "Must-be"
  | "Performance"
  | "Delighter"
  | "Indifferent";

export type ImpactDirection = "positive" | "negative";

export type ActionPriority = "immediate" | "high" | "medium" | "low";

export interface QIEJobResponse {
  job_id: string;
  workflow_id: string;
  status: QIEJobStatus;
  progress: number;
  current_stage: string;
  message: string;
  total_responses: number;
  processed_count: number;
  started_at?: string;
  completed_at?: string;
  error?: string;
}

export interface KeyDriver {
  factor: string;
  impact: ImpactDirection;
  correlation: number;
  description: string;
  evidence_count: number;
  example_quotes: string[];
}

export interface KanoFeature {
  feature_name: string;
  category: KanoCategory;
  satisfaction_impact: number;
  mention_count: number;
  description: string;
}

export interface KanoClassification {
  must_be_features: KanoFeature[];
  performance_features: KanoFeature[];
  delighter_features: KanoFeature[];
  indifferent_features: KanoFeature[];
}

export interface QIESegmentInsight {
  segment_name: string;
  segment_value: string;
  sample_size: number;
  avg_ssr: number;
  avg_sentiment: number;
  top_concerns: string[];
  key_preferences: string[];
}

export interface QIESegmentAnalysis {
  by_age: QIESegmentInsight[];
  by_gender: QIESegmentInsight[];
  by_income: QIESegmentInsight[];
  notable_differences: string[];
}

export interface PainPoint {
  category: SentimentCategory;
  score: number;
  description: string;
  affected_percentage: number;
  example_quotes: string[];
}

export interface ActionItem {
  title: string;
  description: string;
  priority: ActionPriority;
  category: string;
  expected_impact: string;
  related_pain_points: string[];
}

export interface QIEAnalysis {
  executive_summary: string;
  key_drivers: KeyDriver[];
  kano_classification: KanoClassification;
  segment_analysis: QIESegmentAnalysis;
  pain_points: PainPoint[];
  action_items: ActionItem[];
  confidence_score: number;
  analysis_metadata: Record<string, unknown>;
}

export interface CategoryStats {
  category: string;
  count: number;
  percentage: number;
  avg_sentiment: number;
  avg_ssr: number;
  top_keywords: string[];
}

export interface QIEAggregatedStats {
  total_responses: number;
  avg_sentiment: number;
  sentiment_distribution: Record<number, number>;
  category_stats: CategoryStats[];
  keyword_frequency: Record<string, number>;
  segment_breakdown: Record<string, Record<string, { count: number; avg_ssr: number; avg_sentiment: number }>>;
  low_ssr_count: number;
  high_ssr_count: number;
}

export interface QIEResultResponse {
  job_id: string;
  workflow_id: string;
  analysis: QIEAnalysis;
  aggregated_stats: QIEAggregatedStats;
  execution_time: number;
  tier1_time: number;
  tier2_time: number;
  report_data?: ReportData;
  report_generation_time?: number;
}

export interface QIEWebSocketProgress {
  type: "qie_progress";
  progress: number;
  status: QIEJobStatus;
  stage: string;
  message: string;
  processed: number;
  total: number;
}

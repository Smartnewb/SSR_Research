// my-project/frontend/src/lib/report/types.ts

export interface ReportData {
  // Metadata
  conceptId: string;
  conceptName: string;
  generatedAt: string;
  totalRespondents: number;

  // Section 1: Executive Summary
  executiveSummary: {
    oneLiner: string;           // "고객은 ~를 원합니다"
    keyMetrics: {
      respondents: number;
      avgSSR: number;
      confidenceScore: number;
    };
    coreInsights: string[];     // 3-5 bullet points
  };

  // Section 2: Demographics
  demographics: {
    summary: string;            // "20대 초반 도시 거주 대학생..."
    breakdown: {
      age: { label: string; value: string; percentage: number }[];
      gender: { label: string; value: string; percentage: number }[];
      income: { label: string; value: string; percentage: number }[];
      location: { label: string; value: string; percentage: number }[];
    };
  };

  // Section 3: Customer Needs
  customerNeeds: {
    interpretation: string;     // LLM이 작성한 해석 문단
    topNeeds: {
      rank: number;
      keyword: string;
      frequency: number;
      quote: string;            // 대표 인용문
      interpretation: string;   // 이 니즈에 대한 해석
    }[];
  };

  // Section 4: Drivers & Barriers
  driversBarriers: {
    drivers: {
      rank: number;
      factor: string;
      description: string;
      quote: string;
      impactScore: number;      // 0-100
    }[];
    barriers: {
      rank: number;
      factor: string;
      description: string;
      quote: string;
      impactScore: number;      // 0-100
    }[];
  };

  // Section 5: Segment Strategy
  segments: {
    name: string;               // 예: "안전 최우선형"
    description: string;
    message: string;            // 메시지 제안
    offer: string;              // 오퍼 제안
    priorityFeatures: string[]; // 우선 기능
  }[];

  // Section 6: Action Items
  actionItems: {
    priority: 'high' | 'medium' | 'low';
    title: string;
    description: string;
    category: 'product' | 'marketing' | 'operations';
  }[];
}

export interface NarrativeGeneratorInput {
  workflowId: string;
  conceptId: string;
  conceptName: string;
  productDescription: string;
  tier1Results: unknown[];
  aggregatedStats: unknown;
  qieAnalysis: unknown;
  originalResponses: unknown[];
}

export interface NarrativeGeneratorOutput {
  success: boolean;
  reportData: ReportData | null;
  error?: string;
  generationTime: number;
}

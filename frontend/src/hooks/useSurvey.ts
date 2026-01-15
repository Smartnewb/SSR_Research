"use client";

import { useMutation } from "@tanstack/react-query";
import { runSurvey, runABTest } from "@/lib/api";
import type { SurveyRequest, ABTestRequest } from "@/lib/types";

export function useSurveyMutation() {
  return useMutation({
    mutationFn: (request: SurveyRequest) => runSurvey(request),
  });
}

export function useABTestMutation() {
  return useMutation({
    mutationFn: (request: ABTestRequest) => runABTest(request),
  });
}

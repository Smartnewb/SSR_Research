"use client";

import { useState } from "react";
import { SurveyForm } from "@/components/survey/SurveyForm";
import { ResultsDashboard } from "@/components/survey/ResultsDashboard";
import { SurveyProgress } from "@/components/survey/SurveyProgress";
import { useSurveyMutation } from "@/hooks/useSurvey";
import { useWebSocket } from "@/hooks/useWebSocket";
import type { SurveyResponse } from "@/lib/types";
import { toast } from "sonner";

export default function NewSurveyPage() {
  const [results, setResults] = useState<SurveyResponse | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const mutation = useSurveyMutation();

  const ws = useWebSocket({
    onResult: (result) => {
      setResults(result);
      setIsRunning(false);
      toast.success("Survey completed successfully!");
    },
    onError: (error) => {
      setIsRunning(false);
      toast.error(`Survey failed: ${error}`);
    },
  });

  const handleSubmit = async (values: {
    product_description: string;
    sample_size: number;
    use_mock: boolean;
  }) => {
    try {
      setIsRunning(true);
      const result = await mutation.mutateAsync({
        product_description: values.product_description,
        sample_size: values.sample_size,
        use_mock: values.use_mock,
        model: "gpt-4o-mini",
      });
      setResults(result);
      setIsRunning(false);
      toast.success("Survey completed successfully!");
    } catch (error) {
      setIsRunning(false);
      toast.error("Failed to run survey. Make sure the backend is running.");
      console.error(error);
    }
  };

  if (results) {
    return (
      <ResultsDashboard
        results={results}
        onReset={() => {
          setResults(null);
          ws.disconnect();
        }}
      />
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Run Survey</h1>
        <p className="text-muted-foreground">
          Generate synthetic purchase intent scores for your product concept.
        </p>
      </div>

      {isRunning && (
        <SurveyProgress
          status={ws.status}
          progress={ws.progress}
          currentPersona={ws.currentPersona}
          totalPersonas={ws.totalPersonas}
          error={ws.error}
        />
      )}

      <SurveyForm
        onSubmit={handleSubmit}
        isLoading={mutation.isPending || isRunning}
      />
    </div>
  );
}

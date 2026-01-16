"use client";

import { useState, useEffect, useRef } from "react";
import { ABTestForm } from "@/components/survey/ABTestForm";
import { ABTestResults } from "@/components/survey/ABTestResults";
import { SurveyProgress } from "@/components/survey/SurveyProgress";
import { useABTestMutation } from "@/hooks/useSurvey";
import type { ABTestResponse } from "@/lib/types";
import { toast } from "sonner";

export default function ComparePage() {
  const [results, setResults] = useState<ABTestResponse | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [targetProgress, setTargetProgress] = useState(0);
  const mutation = useABTestMutation();
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

  const handleSubmit = async (values: {
    product_a: string;
    product_b: string;
    product_a_name: string;
    product_b_name: string;
    sample_size: number;
    use_mock: boolean;
  }) => {
    try {
      setIsRunning(true);
      setProgress(0);
      setTargetProgress(0);

      const progressInterval = setInterval(() => {
        setTargetProgress((prev) => Math.min(prev + 2, 90));
      }, 200);

      const result = await mutation.mutateAsync({
        product_a: values.product_a,
        product_b: values.product_b,
        product_a_name: values.product_a_name,
        product_b_name: values.product_b_name,
        sample_size: values.sample_size,
        use_mock: values.use_mock,
        model: "gpt-4o-mini",
      });

      clearInterval(progressInterval);
      setTargetProgress(100);
      setTimeout(() => {
        setProgress(100);
        setResults(result);
        setIsRunning(false);
        toast.success("A/B test completed successfully!");
      }, 300);
    } catch (error) {
      setIsRunning(false);
      setProgress(0);
      setTargetProgress(0);
      toast.error("Failed to run A/B test. Make sure the backend is running.");
      console.error(error);
    }
  };

  if (results) {
    return (
      <ABTestResults
        results={results}
        onReset={() => {
          setResults(null);
          setProgress(0);
        }}
      />
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">A/B Testing</h1>
        <p className="text-muted-foreground">
          Compare two product concepts side by side with statistical analysis.
        </p>
      </div>

      {isRunning && (
        <SurveyProgress
          status="running"
          progress={progress}
          currentPersona={Math.floor(progress / 5)}
          totalPersonas={20}
          message="Running A/B test..."
        />
      )}

      <ABTestForm
        onSubmit={handleSubmit}
        isLoading={mutation.isPending || isRunning}
      />
    </div>
  );
}

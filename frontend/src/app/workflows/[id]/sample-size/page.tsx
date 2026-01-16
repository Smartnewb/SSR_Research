"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft } from "lucide-react";

const SAMPLE_SIZES = [
  { value: 100, cost: "$0.50", time: "1 min" },
  { value: 500, cost: "$2.50", time: "4 min" },
  { value: 1000, cost: "$5.00", time: "8 min" },
  { value: 5000, cost: "$25.00", time: "40 min" },
  { value: 10000, cost: "$50.00", time: "80 min" },
];

export default function SampleSizePage() {
  const params = useParams();
  const router = useRouter();
  const workflowId = params.id as string;

  const [selectedSize, setSelectedSize] = useState(100);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/workflows/${workflowId}/sample-size`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sample_size: selectedSize }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to set sample size");
      }

      router.push(`/workflows/${workflowId}/generating`);
    } catch (error) {
      console.error("Error setting sample size:", error);
      alert("Failed to set sample size");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => router.push(`/workflows/${workflowId}/persona`)}
        className="mb-2"
      >
        <ArrowLeft className="h-4 w-4 mr-2" />
        페르소나 수정
      </Button>

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Step 4: Select Sample Size</h1>
        <div className="text-sm text-muted-foreground">Step 4 of 7</div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>How many synthetic personas to generate?</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            {SAMPLE_SIZES.map((option) => (
              <div
                key={option.value}
                className={`border rounded-lg p-4 cursor-pointer transition ${
                  selectedSize === option.value
                    ? "border-primary bg-primary/5"
                    : "hover:border-primary/50"
                }`}
                onClick={() => setSelectedSize(option.value)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <input
                      type="radio"
                      checked={selectedSize === option.value}
                      onChange={() => setSelectedSize(option.value)}
                    />
                    <div>
                      <div className="font-semibold">
                        {option.value.toLocaleString()} Personas
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Estimated time: {option.time}
                      </div>
                    </div>
                  </div>
                  <div className="text-lg font-bold">{option.cost}</div>
                </div>
              </div>
            ))}
          </div>

          <div className="bg-muted/50 p-4 rounded-lg space-y-2">
            <h4 className="font-semibold text-sm">Note</h4>
            <p className="text-sm text-muted-foreground">
              Larger samples provide more statistically significant results but
              take longer to process. We recommend starting with 100-500 for
              initial testing.
            </p>
          </div>

          <Button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full"
            size="lg"
          >
            {loading ? "Setting up..." : "Generate Personas"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

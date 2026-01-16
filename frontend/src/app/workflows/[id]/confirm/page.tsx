"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft } from "lucide-react";

export default function ConfirmPersonaPage() {
  const params = useParams();
  const router = useRouter();
  const workflowId = params.id as string;

  const [workflow, setWorkflow] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    const fetchWorkflow = async () => {
      try {
        const response = await fetch(
          `http://localhost:8000/api/workflows/${workflowId}`
        );
        const data = await response.json();
        setWorkflow(data);
      } catch (error) {
        console.error("Error fetching workflow:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchWorkflow();
  }, [workflowId]);

  const handleConfirm = async () => {
    setConfirming(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/workflows/${workflowId}/confirm`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        throw new Error("Failed to confirm persona");
      }

      router.push(`/workflows/${workflowId}/sample-size`);
    } catch (error) {
      console.error("Error confirming persona:", error);
      alert("Failed to confirm persona");
    } finally {
      setConfirming(false);
    }
  };

  const handleEdit = () => {
    router.push(`/workflows/${workflowId}/persona`);
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!workflow || !workflow.core_persona) {
    return <div>Persona not found</div>;
  }

  const persona = workflow.core_persona;

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
        <h1 className="text-2xl font-bold">Step 3: Confirm Core Persona</h1>
        <div className="text-sm text-muted-foreground">Step 3 of 7</div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Review Your Core Persona</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <div className="text-sm font-semibold">Age Range</div>
              <div className="text-sm text-muted-foreground">
                {persona.age_range[0]} - {persona.age_range[1]} years
              </div>
            </div>

            <div className="space-y-1">
              <div className="text-sm font-semibold">Location</div>
              <div className="text-sm text-muted-foreground capitalize">
                {persona.location}
              </div>
            </div>
          </div>

          <div className="space-y-1">
            <div className="text-sm font-semibold">Gender Distribution</div>
            <div className="text-sm text-muted-foreground">
              {Object.entries(persona.gender_distribution)
                .map(([k, v]) => {
                  const val = v as number;
                  const percent = val <= 1 ? Math.round(val * 100) : val;
                  return `${k}: ${percent}%`;
                })
                .join(", ")}
            </div>
          </div>

          <div className="space-y-1">
            <div className="text-sm font-semibold">Income Brackets</div>
            <div className="text-sm text-muted-foreground">
              {Object.entries(persona.income_brackets)
                .map(([k, v]) => {
                  const val = v as number;
                  const percent = val <= 1 ? Math.round(val * 100) : val;
                  return `${k}: ${percent}%`;
                })
                .join(", ")}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <div className="text-sm font-semibold">Category Usage</div>
              <div className="text-sm text-muted-foreground capitalize">
                {persona.category_usage}
              </div>
            </div>

            <div className="space-y-1">
              <div className="text-sm font-semibold">Shopping Behavior</div>
              <div className="text-sm text-muted-foreground capitalize">
                {persona.shopping_behavior.replace("_", " ")}
              </div>
            </div>
          </div>

          <div className="space-y-1">
            <div className="text-sm font-semibold">Key Pain Points</div>
            <ul className="text-sm text-muted-foreground list-disc list-inside">
              {persona.key_pain_points.map((point: string) => (
                <li key={point}>{point}</li>
              ))}
            </ul>
          </div>

          <div className="space-y-1">
            <div className="text-sm font-semibold">Decision Drivers</div>
            <ul className="text-sm text-muted-foreground list-disc list-inside">
              {persona.decision_drivers.map((driver: string) => (
                <li key={driver}>{driver}</li>
              ))}
            </ul>
          </div>

          <div className="flex gap-2 pt-4">
            <Button onClick={handleEdit} variant="outline" className="flex-1">
              Edit Persona
            </Button>
            <Button
              onClick={handleConfirm}
              disabled={confirming}
              className="flex-1"
            >
              {confirming ? "Confirming..." : "Confirm & Continue"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

"use client";

import { Progress } from "@/components/ui/progress";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2, CheckCircle2, XCircle, Users } from "lucide-react";

interface SurveyProgressProps {
  status: string;
  progress: number;
  currentPersona: number;
  totalPersonas: number;
  error?: string | null;
  message?: string;
}

export function SurveyProgress({
  status,
  progress,
  currentPersona,
  totalPersonas,
  error,
  message,
}: SurveyProgressProps) {
  const getStatusIcon = () => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case "error":
        return <XCircle className="h-5 w-5 text-red-500" />;
      case "idle":
        return null;
      default:
        return <Loader2 className="h-5 w-5 animate-spin text-blue-500" />;
    }
  };

  const getStatusText = () => {
    if (message) return message;
    switch (status) {
      case "idle":
        return "Ready to start";
      case "connecting":
        return "Connecting...";
      case "connected":
        return "Connected";
      case "running":
        return `Processing persona ${currentPersona} of ${totalPersonas}`;
      case "completed":
        return "Survey completed!";
      case "error":
        return error || "An error occurred";
      case "reconnecting":
        return "Reconnecting...";
      default:
        return status;
    }
  };

  if (status === "idle") {
    return null;
  }

  return (
    <Card className="mb-6">
      <CardContent className="pt-6">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {getStatusIcon()}
              <span className="font-medium">{getStatusText()}</span>
            </div>
            <span className="text-sm text-muted-foreground">
              {Math.round(progress)}%
            </span>
          </div>

          <Progress value={progress} className="h-2" />

          {status === "running" && totalPersonas > 0 && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Users className="h-4 w-4" />
              <span>
                Surveying synthetic personas ({currentPersona}/{totalPersonas})
              </span>
            </div>
          )}

          {status === "error" && error && (
            <p className="text-sm text-red-500">{error}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

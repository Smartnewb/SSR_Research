"use client";

import { useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ChevronDown, ChevronUp } from "lucide-react";
import type { SurveyResultItem } from "@/lib/types";
import { getScoreColor, getScoreBgColor } from "@/lib/api";

interface ResponseTableProps {
  results: SurveyResultItem[];
}

export function ResponseTable({ results }: ResponseTableProps) {
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [sortField, setSortField] = useState<"ssr_score" | "persona_id">("ssr_score");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const toggleRow = (id: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedRows(newExpanded);
  };

  const handleSort = (field: "ssr_score" | "persona_id") => {
    if (sortField === field) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDir("desc");
    }
  };

  const sortedResults = [...results].sort((a, b) => {
    const multiplier = sortDir === "asc" ? 1 : -1;
    if (sortField === "ssr_score") {
      return (a.ssr_score - b.ssr_score) * multiplier;
    }
    return a.persona_id.localeCompare(b.persona_id) * multiplier;
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Responses ({results.length})</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead
                className="cursor-pointer hover:bg-muted"
                onClick={() => handleSort("persona_id")}
              >
                Persona {sortField === "persona_id" && (sortDir === "asc" ? "↑" : "↓")}
              </TableHead>
              <TableHead
                className="cursor-pointer hover:bg-muted"
                onClick={() => handleSort("ssr_score")}
              >
                SSR Score {sortField === "ssr_score" && (sortDir === "asc" ? "↑" : "↓")}
              </TableHead>
              <TableHead>Likert (1-5)</TableHead>
              <TableHead>Response</TableHead>
              <TableHead></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedResults.map((result) => (
              <>
                <TableRow key={result.persona_id}>
                  <TableCell className="font-mono text-sm">
                    {result.persona_id.slice(0, 12)}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="secondary"
                      className={getScoreBgColor(result.ssr_score)}
                    >
                      <span className={getScoreColor(result.ssr_score)}>
                        {(result.ssr_score * 100).toFixed(1)}%
                      </span>
                    </Badge>
                  </TableCell>
                  <TableCell>{result.likert_5.toFixed(1)}</TableCell>
                  <TableCell className="max-w-[300px] truncate">
                    {result.response_text}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleRow(result.persona_id)}
                    >
                      {expandedRows.has(result.persona_id) ? (
                        <ChevronUp className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )}
                    </Button>
                  </TableCell>
                </TableRow>
                {expandedRows.has(result.persona_id) && (
                  <TableRow key={`${result.persona_id}-expanded`}>
                    <TableCell colSpan={5} className="bg-muted/50">
                      <div className="p-4 space-y-2">
                        <p className="text-sm">
                          <strong>Full Response:</strong>
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {result.response_text}
                        </p>
                        {result.persona_data && (
                          <div className="flex flex-wrap gap-2 mt-2">
                            {Object.entries(result.persona_data).map(([key, value]) => (
                              <Badge key={key} variant="outline">
                                {key}: {String(value)}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                )}
              </>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

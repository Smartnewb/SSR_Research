"use client";

import { useState } from "react";
import { pdf } from "@react-pdf/renderer";
import { saveAs } from "file-saver";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Download,
  FileText,
  Users,
  TrendingUp,
  TrendingDown,
  Target,
  CheckSquare,
  Loader2,
} from "lucide-react";
import { toast } from "sonner";
import { ReportPDF } from "./ReportPDF";
import type { ReportData } from "@/lib/report/types";

interface InsightReportProps {
  data: ReportData;
  onExportCSV?: () => void;
}

export function InsightReport({ data, onExportCSV }: InsightReportProps) {
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);

  const handleDownloadPDF = async () => {
    setIsGeneratingPDF(true);
    try {
      const blob = await pdf(<ReportPDF data={data} />).toBlob();
      saveAs(blob, `insight-report-${data.conceptId}.pdf`);
      toast.success("PDF 다운로드 완료!");
    } catch (error) {
      console.error("PDF generation failed:", error);
      toast.error("PDF 생성 실패. 다시 시도해주세요.");
    } finally {
      setIsGeneratingPDF(false);
    }
  };

  const formatDate = (isoString: string) => {
    return new Date(isoString).toLocaleDateString("ko-KR", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="space-y-6">
      {/* Header with Export Buttons */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold">{data.conceptName}</h2>
          <p className="text-sm text-muted-foreground">
            생성일: {formatDate(data.generatedAt)}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleDownloadPDF}
            disabled={isGeneratingPDF}
          >
            {isGeneratingPDF ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Download className="h-4 w-4 mr-2" />
            )}
            PDF 다운로드
          </Button>
          {onExportCSV && (
            <Button variant="outline" onClick={onExportCSV}>
              <FileText className="h-4 w-4 mr-2" />
              CSV 다운로드
            </Button>
          )}
        </div>
      </div>

      {/* Section 1: Executive Summary */}
      <Card className="border-indigo-200 bg-indigo-50/30">
        <CardHeader>
          <CardTitle className="text-lg text-indigo-700">
            Executive Summary
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-lg font-medium p-4 bg-white rounded-lg border">
            &quot;{data.executiveSummary.oneLiner}&quot;
          </p>

          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-white rounded-lg">
              <div className="text-3xl font-bold text-indigo-600">
                {data.executiveSummary.keyMetrics.respondents}
              </div>
              <div className="text-xs text-muted-foreground">응답자 수</div>
            </div>
            <div className="text-center p-4 bg-white rounded-lg">
              <div className="text-3xl font-bold text-indigo-600">
                {(data.executiveSummary.keyMetrics.avgSSR * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-muted-foreground">평균 SSR</div>
            </div>
            <div className="text-center p-4 bg-white rounded-lg">
              <div className="text-3xl font-bold text-indigo-600">
                {(data.executiveSummary.keyMetrics.confidenceScore * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-muted-foreground">신뢰도</div>
            </div>
          </div>

          <div className="space-y-2">
            <p className="text-sm font-medium text-muted-foreground">
              핵심 인사이트
            </p>
            <ul className="space-y-2">
              {data.executiveSummary.coreInsights.map((insight, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-indigo-500 mt-1">•</span>
                  <span>{insight}</span>
                </li>
              ))}
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Section 2: Demographics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            고객 프로필
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground mb-4">{data.demographics.summary}</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {data.demographics.breakdown.age.slice(0, 4).map((item, i) => (
              <div key={i} className="p-3 bg-muted/30 rounded-lg">
                <div className="text-sm font-medium">{item.value}</div>
                <div className="text-2xl font-bold">
                  {item.percentage.toFixed(0)}%
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Section 3: Customer Needs */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            핵심 니즈 TOP 5
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-muted-foreground">
            {data.customerNeeds.interpretation}
          </p>
          <Separator />
          {data.customerNeeds.topNeeds.map((need) => (
            <div key={need.rank} className="space-y-2 p-4 bg-muted/20 rounded-lg">
              <div className="flex items-center gap-3">
                <Badge variant="outline" className="text-lg px-3 py-1">
                  #{need.rank}
                </Badge>
                <span className="font-semibold text-lg">{need.keyword}</span>
                <span className="text-muted-foreground text-sm">
                  (빈도: {need.frequency})
                </span>
              </div>
              <blockquote className="border-l-4 border-muted-foreground/30 pl-4 italic text-muted-foreground">
                &quot;{need.quote}&quot;
              </blockquote>
              <p className="text-sm">{need.interpretation}</p>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Section 4: Drivers & Barriers */}
      <div className="grid md:grid-cols-2 gap-6">
        <Card className="border-green-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-700">
              <TrendingUp className="h-5 w-5" />
              구매 촉진 요인 TOP 5
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {data.driversBarriers.drivers.map((driver) => (
              <div key={driver.rank} className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-medium">
                    #{driver.rank} {driver.factor}
                  </span>
                  <Badge className="bg-green-100 text-green-700">
                    {driver.impactScore}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground">
                  {driver.description}
                </p>
                <blockquote className="text-xs italic text-muted-foreground border-l-2 border-green-300 pl-2">
                  &quot;{driver.quote}&quot;
                </blockquote>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="border-red-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-700">
              <TrendingDown className="h-5 w-5" />
              구매 저해 요인 TOP 5
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {data.driversBarriers.barriers.map((barrier) => (
              <div key={barrier.rank} className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-medium">
                    #{barrier.rank} {barrier.factor}
                  </span>
                  <Badge className="bg-red-100 text-red-700">
                    {barrier.impactScore}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground">
                  {barrier.description}
                </p>
                <blockquote className="text-xs italic text-muted-foreground border-l-2 border-red-300 pl-2">
                  &quot;{barrier.quote}&quot;
                </blockquote>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Section 5: Segments */}
      <Card>
        <CardHeader>
          <CardTitle>세그먼트별 전략</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.segments.map((segment, i) => (
              <div
                key={i}
                className="p-4 border rounded-lg space-y-2 hover:shadow-md transition-shadow"
              >
                <h4 className="font-semibold text-lg">{segment.name}</h4>
                <p className="text-sm text-muted-foreground">
                  {segment.description}
                </p>
                <Separator />
                <div className="space-y-1 text-sm">
                  <p>
                    <span className="font-medium">메시지:</span> {segment.message}
                  </p>
                  <p>
                    <span className="font-medium">오퍼:</span> {segment.offer}
                  </p>
                  <p>
                    <span className="font-medium">우선 기능:</span>{" "}
                    {segment.priorityFeatures.join(", ")}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Section 6: Action Items */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckSquare className="h-5 w-5" />
            실행 액션 아이템
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {data.actionItems.map((item, i) => (
              <div
                key={i}
                className="flex items-start gap-3 p-3 border rounded-lg"
              >
                <Badge
                  variant={
                    item.priority === "high"
                      ? "destructive"
                      : item.priority === "medium"
                      ? "default"
                      : "secondary"
                  }
                >
                  {item.priority === "high"
                    ? "높음"
                    : item.priority === "medium"
                    ? "중간"
                    : "낮음"}
                </Badge>
                <div className="flex-1">
                  <p className="font-medium">{item.title}</p>
                  <p className="text-sm text-muted-foreground">
                    {item.description}
                  </p>
                </div>
                <Badge variant="outline">
                  {item.category === "product"
                    ? "제품"
                    : item.category === "marketing"
                    ? "마케팅"
                    : "운영"}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

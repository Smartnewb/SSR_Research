"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { CheckCircle2, AlertTriangle, Clock, ArrowRight } from "lucide-react";
import { useState } from "react";
import type { ActionItem, ActionPriority } from "@/lib/types";

interface ActionItemsListProps {
  actionItems: ActionItem[];
}

const PRIORITY_CONFIG: Record<ActionPriority, { label: string; color: string; icon: React.ElementType }> = {
  immediate: {
    label: "즉시 개선",
    color: "bg-red-500 text-white",
    icon: AlertTriangle,
  },
  high: {
    label: "높음",
    color: "bg-orange-500 text-white",
    icon: ArrowRight,
  },
  medium: {
    label: "중간",
    color: "bg-yellow-500 text-white",
    icon: Clock,
  },
  low: {
    label: "낮음",
    color: "bg-gray-400 text-white",
    icon: Clock,
  },
};

export function ActionItemsList({ actionItems }: ActionItemsListProps) {
  const [checkedItems, setCheckedItems] = useState<Set<number>>(new Set());

  const handleToggle = (index: number) => {
    const newChecked = new Set(checkedItems);
    if (newChecked.has(index)) {
      newChecked.delete(index);
    } else {
      newChecked.add(index);
    }
    setCheckedItems(newChecked);
  };

  // Group by priority
  const immediateItems = actionItems.filter((item) => item.priority === "immediate");
  const highItems = actionItems.filter((item) => item.priority === "high");
  const mediumItems = actionItems.filter((item) => item.priority === "medium");
  const lowItems = actionItems.filter((item) => item.priority === "low");

  const completedCount = checkedItems.size;
  const totalCount = actionItems.length;
  const progress = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;

  const renderActionItem = (item: ActionItem, globalIndex: number) => {
    const config = PRIORITY_CONFIG[item.priority];
    const Icon = config.icon;
    const isChecked = checkedItems.has(globalIndex);

    return (
      <div
        key={globalIndex}
        className={`flex items-start gap-3 p-3 rounded-lg border transition-all ${
          isChecked ? "bg-muted/50 opacity-60" : "bg-white hover:bg-muted/30"
        }`}
      >
        <Checkbox
          checked={isChecked}
          onCheckedChange={() => handleToggle(globalIndex)}
          className="mt-0.5"
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className={`font-medium ${isChecked ? "line-through text-muted-foreground" : ""}`}
            >
              {item.title}
            </span>
            <Badge className={config.color} variant="secondary">
              <Icon className="h-3 w-3 mr-1" />
              {config.label}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-1">{item.description}</p>
          {item.expected_impact && (
            <p className="text-xs text-blue-600 mt-1">
              기대 효과: {item.expected_impact}
            </p>
          )}
          {item.related_pain_points.length > 0 && (
            <div className="flex gap-1 mt-2 flex-wrap">
              {item.related_pain_points.map((point, idx) => (
                <Badge key={idx} variant="outline" className="text-xs">
                  {point}
                </Badge>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  let globalIndex = 0;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-500" />
            <CardTitle>Action Items</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              {completedCount}/{totalCount} 완료
            </span>
            <div className="w-20 h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500 transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>
        <CardDescription>
          분석 결과를 바탕으로 한 개선 권장 사항 (우선순위별 정렬)
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Immediate Items */}
        {immediateItems.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-red-500" />
              <h4 className="text-sm font-medium text-red-600">
                즉시 개선 필요 ({immediateItems.length})
              </h4>
            </div>
            <div className="space-y-2 pl-6">
              {immediateItems.map((item) => {
                const currentIndex = globalIndex++;
                return renderActionItem(item, currentIndex);
              })}
            </div>
          </div>
        )}

        {/* High Priority Items */}
        {highItems.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-orange-600">
              높은 우선순위 ({highItems.length})
            </h4>
            <div className="space-y-2">
              {highItems.map((item) => {
                const currentIndex = globalIndex++;
                return renderActionItem(item, currentIndex);
              })}
            </div>
          </div>
        )}

        {/* Medium Priority Items */}
        {mediumItems.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-yellow-600">
              중간 우선순위 ({mediumItems.length})
            </h4>
            <div className="space-y-2">
              {mediumItems.map((item) => {
                const currentIndex = globalIndex++;
                return renderActionItem(item, currentIndex);
              })}
            </div>
          </div>
        )}

        {/* Low Priority Items */}
        {lowItems.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-600">
              낮은 우선순위 ({lowItems.length})
            </h4>
            <div className="space-y-2">
              {lowItems.map((item) => {
                const currentIndex = globalIndex++;
                return renderActionItem(item, currentIndex);
              })}
            </div>
          </div>
        )}

        {actionItems.length === 0 && (
          <p className="text-center text-muted-foreground py-8">
            추천 Action Item이 없습니다.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

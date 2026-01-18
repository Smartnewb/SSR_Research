"use client";

import {
  Document,
  Page,
  Text,
  View,
  StyleSheet,
  Font,
} from "@react-pdf/renderer";
import type { ReportData } from "@/lib/report/types";

// Register Korean font
Font.register({
  family: "NotoSansKR",
  src: "/fonts/NotoSansKR-Regular.otf",
});

const styles = StyleSheet.create({
  page: {
    padding: 40,
    fontFamily: "NotoSansKR",
    fontSize: 10,
    lineHeight: 1.6,
  },
  header: {
    marginBottom: 20,
    borderBottomWidth: 2,
    borderBottomColor: "#6366f1",
    paddingBottom: 10,
  },
  title: {
    fontSize: 20,
    fontWeight: "bold",
    color: "#1f2937",
  },
  subtitle: {
    fontSize: 10,
    color: "#6b7280",
    marginTop: 4,
  },
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: "bold",
    color: "#4f46e5",
    marginBottom: 10,
    paddingBottom: 4,
    borderBottomWidth: 1,
    borderBottomColor: "#e5e7eb",
  },
  oneLiner: {
    fontSize: 12,
    fontWeight: "bold",
    color: "#1f2937",
    marginBottom: 12,
    padding: 12,
    backgroundColor: "#f3f4f6",
    borderRadius: 4,
  },
  metricsRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 12,
  },
  metricBox: {
    width: "30%",
    padding: 10,
    backgroundColor: "#eef2ff",
    borderRadius: 4,
    textAlign: "center",
  },
  metricValue: {
    fontSize: 18,
    fontWeight: "bold",
    color: "#4f46e5",
  },
  metricLabel: {
    fontSize: 8,
    color: "#6b7280",
    marginTop: 2,
  },
  bulletList: {
    marginLeft: 10,
  },
  bulletItem: {
    flexDirection: "row",
    marginBottom: 4,
  },
  bullet: {
    width: 15,
    color: "#4f46e5",
  },
  bulletText: {
    flex: 1,
  },
  table: {
    width: "100%",
    marginBottom: 10,
  },
  tableRow: {
    flexDirection: "row",
    borderBottomWidth: 1,
    borderBottomColor: "#e5e7eb",
    paddingVertical: 6,
  },
  tableHeader: {
    backgroundColor: "#f3f4f6",
    fontWeight: "bold",
  },
  tableCell: {
    flex: 1,
    paddingHorizontal: 4,
  },
  tableCellSmall: {
    width: 40,
    paddingHorizontal: 4,
    textAlign: "center",
  },
  quote: {
    color: "#6b7280",
    fontSize: 9,
    marginTop: 4,
    paddingLeft: 10,
    borderLeftWidth: 2,
    borderLeftColor: "#4f46e5",
  },
  segmentCard: {
    marginBottom: 12,
    padding: 10,
    backgroundColor: "#fafafa",
    borderRadius: 4,
    borderWidth: 1,
    borderColor: "#e5e7eb",
  },
  segmentName: {
    fontSize: 11,
    fontWeight: "bold",
    color: "#1f2937",
    marginBottom: 4,
  },
  segmentDetail: {
    fontSize: 9,
    color: "#4b5563",
    marginBottom: 2,
  },
  actionItem: {
    flexDirection: "row",
    marginBottom: 8,
    padding: 8,
    backgroundColor: "#fafafa",
    borderRadius: 4,
  },
  priorityBadge: {
    width: 50,
    padding: 2,
    borderRadius: 2,
    textAlign: "center",
    fontSize: 8,
    marginRight: 8,
  },
  priorityHigh: {
    backgroundColor: "#fef2f2",
    color: "#dc2626",
  },
  priorityMedium: {
    backgroundColor: "#fffbeb",
    color: "#d97706",
  },
  priorityLow: {
    backgroundColor: "#f0fdf4",
    color: "#16a34a",
  },
  footer: {
    position: "absolute",
    bottom: 30,
    left: 40,
    right: 40,
    textAlign: "center",
    fontSize: 8,
    color: "#9ca3af",
  },
  pageNumber: {
    position: "absolute",
    bottom: 30,
    right: 40,
    fontSize: 8,
    color: "#9ca3af",
  },
});

interface ReportPDFProps {
  data: ReportData;
}

export function ReportPDF({ data }: ReportPDFProps) {
  const formatDate = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleDateString("ko-KR", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  return (
    <Document>
      {/* Page 1: Executive Summary */}
      <Page size="A4" style={styles.page}>
        <View style={styles.header}>
          <Text style={styles.title}>
            {data.conceptName} 설문 인사이트 보고서
          </Text>
          <Text style={styles.subtitle}>
            생성일: {formatDate(data.generatedAt)}
          </Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Executive Summary</Text>
          <Text style={styles.oneLiner}>
            {data.executiveSummary.oneLiner}
          </Text>

          <View style={styles.metricsRow}>
            <View style={styles.metricBox}>
              <Text style={styles.metricValue}>
                {data.executiveSummary.keyMetrics.respondents}
              </Text>
              <Text style={styles.metricLabel}>응답자 수</Text>
            </View>
            <View style={styles.metricBox}>
              <Text style={styles.metricValue}>
                {(data.executiveSummary.keyMetrics.avgSSR * 100).toFixed(1)}%
              </Text>
              <Text style={styles.metricLabel}>평균 SSR</Text>
            </View>
            <View style={styles.metricBox}>
              <Text style={styles.metricValue}>
                {(data.executiveSummary.keyMetrics.confidenceScore * 100).toFixed(0)}%
              </Text>
              <Text style={styles.metricLabel}>신뢰도</Text>
            </View>
          </View>

          <View style={styles.bulletList}>
            {data.executiveSummary.coreInsights.map((insight, i) => (
              <View key={i} style={styles.bulletItem}>
                <Text style={styles.bullet}>•</Text>
                <Text style={styles.bulletText}>{insight}</Text>
              </View>
            ))}
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>고객 프로필</Text>
          <Text style={{ marginBottom: 8 }}>{data.demographics.summary}</Text>

          <View style={styles.table}>
            <View style={[styles.tableRow, styles.tableHeader]}>
              <Text style={styles.tableCell}>구분</Text>
              <Text style={styles.tableCell}>값</Text>
              <Text style={styles.tableCellSmall}>비율</Text>
            </View>
            {data.demographics.breakdown.age.map((item, i) => (
              <View key={i} style={styles.tableRow}>
                <Text style={styles.tableCell}>연령</Text>
                <Text style={styles.tableCell}>{item.value}</Text>
                <Text style={styles.tableCellSmall}>
                  {item.percentage.toFixed(0)}%
                </Text>
              </View>
            ))}
            {data.demographics.breakdown.gender.map((item, i) => (
              <View key={i} style={styles.tableRow}>
                <Text style={styles.tableCell}>성별</Text>
                <Text style={styles.tableCell}>{item.value}</Text>
                <Text style={styles.tableCellSmall}>
                  {item.percentage.toFixed(0)}%
                </Text>
              </View>
            ))}
          </View>
        </View>

        <Text style={styles.pageNumber}>1</Text>
      </Page>

      {/* Page 2: Customer Needs */}
      <Page size="A4" style={styles.page}>
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>핵심 니즈 TOP 5</Text>
          <Text style={{ marginBottom: 12 }}>
            {data.customerNeeds.interpretation}
          </Text>

          {data.customerNeeds.topNeeds.map((need) => (
            <View key={need.rank} style={{ marginBottom: 12 }}>
              <View style={{ flexDirection: "row", alignItems: "center" }}>
                <Text style={{ fontWeight: "bold", marginRight: 8 }}>
                  #{need.rank}
                </Text>
                <Text style={{ fontWeight: "bold" }}>{need.keyword}</Text>
                <Text style={{ color: "#6b7280", marginLeft: 8 }}>
                  (빈도: {need.frequency})
                </Text>
              </View>
              <Text style={styles.quote}>&quot;{need.quote}&quot;</Text>
              <Text style={{ marginTop: 4, fontSize: 9 }}>
                {need.interpretation}
              </Text>
            </View>
          ))}
        </View>

        <Text style={styles.pageNumber}>2</Text>
      </Page>

      {/* Page 3: Drivers & Barriers */}
      <Page size="A4" style={styles.page}>
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>구매 촉진 요인 TOP 5</Text>
          {data.driversBarriers.drivers.map((driver) => (
            <View key={driver.rank} style={{ marginBottom: 10 }}>
              <View style={{ flexDirection: "row", alignItems: "center" }}>
                <Text style={{ fontWeight: "bold", marginRight: 8 }}>
                  #{driver.rank}
                </Text>
                <Text style={{ fontWeight: "bold", flex: 1 }}>
                  {driver.factor}
                </Text>
                <Text style={{ color: "#16a34a" }}>
                  영향도: {driver.impactScore}
                </Text>
              </View>
              <Text style={{ fontSize: 9, marginTop: 2 }}>
                {driver.description}
              </Text>
              <Text style={styles.quote}>&quot;{driver.quote}&quot;</Text>
            </View>
          ))}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>구매 저해 요인 TOP 5</Text>
          {data.driversBarriers.barriers.map((barrier) => (
            <View key={barrier.rank} style={{ marginBottom: 10 }}>
              <View style={{ flexDirection: "row", alignItems: "center" }}>
                <Text style={{ fontWeight: "bold", marginRight: 8 }}>
                  #{barrier.rank}
                </Text>
                <Text style={{ fontWeight: "bold", flex: 1 }}>
                  {barrier.factor}
                </Text>
                <Text style={{ color: "#dc2626" }}>
                  영향도: {barrier.impactScore}
                </Text>
              </View>
              <Text style={{ fontSize: 9, marginTop: 2 }}>
                {barrier.description}
              </Text>
              <Text style={styles.quote}>&quot;{barrier.quote}&quot;</Text>
            </View>
          ))}
        </View>

        <Text style={styles.pageNumber}>3</Text>
      </Page>

      {/* Page 4: Segments & Actions */}
      <Page size="A4" style={styles.page}>
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>세그먼트별 전략</Text>
          {data.segments.map((segment, i) => (
            <View key={i} style={styles.segmentCard}>
              <Text style={styles.segmentName}>{segment.name}</Text>
              <Text style={styles.segmentDetail}>{segment.description}</Text>
              <Text style={styles.segmentDetail}>
                메시지: {segment.message}
              </Text>
              <Text style={styles.segmentDetail}>오퍼: {segment.offer}</Text>
              <Text style={styles.segmentDetail}>
                우선 기능: {segment.priorityFeatures.join(", ")}
              </Text>
            </View>
          ))}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>실행 액션 아이템</Text>
          {data.actionItems.map((item, i) => (
            <View key={i} style={styles.actionItem}>
              <Text
                style={[
                  styles.priorityBadge,
                  item.priority === "high"
                    ? styles.priorityHigh
                    : item.priority === "medium"
                    ? styles.priorityMedium
                    : styles.priorityLow,
                ]}
              >
                {item.priority === "high"
                  ? "높음"
                  : item.priority === "medium"
                  ? "중간"
                  : "낮음"}
              </Text>
              <View style={{ flex: 1 }}>
                <Text style={{ fontWeight: "bold", marginBottom: 2 }}>
                  {item.title}
                </Text>
                <Text style={{ fontSize: 9, color: "#4b5563" }}>
                  {item.description}
                </Text>
                <Text style={{ fontSize: 8, color: "#9ca3af", marginTop: 2 }}>
                  담당: {item.category === "product" ? "제품팀" : item.category === "marketing" ? "마케팅팀" : "운영팀"}
                </Text>
              </View>
            </View>
          ))}
        </View>

        <Text style={styles.footer}>
          SSR Market Research Tool로 생성됨
        </Text>
        <Text style={styles.pageNumber}>4</Text>
      </Page>
    </Document>
  );
}

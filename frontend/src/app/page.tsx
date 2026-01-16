import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart3, Zap, DollarSign, Users } from "lucide-react";
import Link from "next/link";

export default function Home() {
  return (
    <div className="space-y-12">
      <section className="text-center py-12">
        <h1 className="text-4xl font-bold mb-4">
          Synthetic Market Research
        </h1>
        <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
          Generate synthetic purchase intent data using the Semantic Similarity
          Rating (SSR) method. Get actionable insights in minutes, not weeks.
        </p>
        <div className="flex gap-4 justify-center">
          <Link href="/workflows/new">
            <Button size="lg">Run Survey</Button>
          </Link>
        </div>
        <p className="text-sm text-muted-foreground mt-4">
          단일 설문, A/B 테스팅, Multi-Concept 비교를 모두 지원합니다
        </p>
      </section>

      <section className="grid md:grid-cols-4 gap-6">
        <Card>
          <CardHeader>
            <Zap className="h-10 w-10 text-yellow-500 mb-2" />
            <CardTitle>Fast Results</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              Get results in under 2 minutes for 100 synthetic respondents.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <DollarSign className="h-10 w-10 text-green-500 mb-2" />
            <CardTitle>Cost Effective</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              Less than $1 per 100 respondents. No survey panels needed.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <BarChart3 className="h-10 w-10 text-blue-500 mb-2" />
            <CardTitle>High Correlation</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              &gt;0.9 correlation with human purchase intent behavior.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <Users className="h-10 w-10 text-purple-500 mb-2" />
            <CardTitle>Diverse Personas</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              Synthetic personas with realistic demographic profiles.
            </p>
          </CardContent>
        </Card>
      </section>

      <section className="bg-muted/50 rounded-lg p-8">
        <h2 className="text-2xl font-bold mb-4">How It Works</h2>
        <div className="grid md:grid-cols-3 gap-6">
          <div className="space-y-2">
            <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
              1
            </div>
            <h3 className="font-semibold">Describe Your Product</h3>
            <p className="text-sm text-muted-foreground">
              Enter your product concept, including features and pricing.
            </p>
          </div>
          <div className="space-y-2">
            <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
              2
            </div>
            <h3 className="font-semibold">Generate Responses</h3>
            <p className="text-sm text-muted-foreground">
              AI personas provide free-text opinions about your product.
            </p>
          </div>
          <div className="space-y-2">
            <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
              3
            </div>
            <h3 className="font-semibold">Get SSR Scores</h3>
            <p className="text-sm text-muted-foreground">
              Semantic similarity calculates purchase intent scores.
            </p>
          </div>
        </div>
      </section>

      <section className="text-center">
        <h2 className="text-2xl font-bold mb-4">Ready to Start?</h2>
        <p className="text-muted-foreground mb-6">
          Try mock mode first - no API key required!
        </p>
        <Link href="/workflows/new">
          <Button size="lg">Create Your First Survey</Button>
        </Link>
      </section>
    </div>
  );
}

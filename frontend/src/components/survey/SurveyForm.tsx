"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Loader2 } from "lucide-react";

const surveyFormSchema = z.object({
  product_description: z
    .string()
    .min(10, "Product description must be at least 10 characters")
    .max(2000, "Product description must be less than 2000 characters"),
  sample_size: z.number().min(5).max(200),
  use_mock: z.boolean(),
});

type SurveyFormValues = z.infer<typeof surveyFormSchema>;

interface SurveyFormProps {
  onSubmit: (values: SurveyFormValues) => void;
  isLoading?: boolean;
}

const exampleProducts = [
  "Smart coffee mug that keeps your drink at the perfect temperature all day. Features app control and battery lasts 3 hours. Price: $79.",
  "Premium noise-cancelling headphones with 40-hour battery life and spatial audio. Price: $349.",
  "AI-powered fitness tracker that provides personalized workout recommendations. Price: $199.",
  "Eco-friendly water bottle that purifies water using UV light. Price: $45.",
];

export function SurveyForm({ onSubmit, isLoading = false }: SurveyFormProps) {
  const form = useForm<SurveyFormValues>({
    resolver: zodResolver(surveyFormSchema),
    defaultValues: {
      product_description: "",
      sample_size: 20,
      use_mock: true,
    },
  });

  const productDescription = form.watch("product_description");
  const sampleSize = form.watch("sample_size");
  const useMock = form.watch("use_mock");

  const estimatedCost = useMock ? 0 : sampleSize * 0.005;
  const estimatedTime = useMock ? sampleSize * 0.1 : sampleSize * 1.5;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Run Survey</CardTitle>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <FormField
              control={form.control}
              name="product_description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Product Description</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Describe your product concept..."
                      className="min-h-[120px]"
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    {productDescription.length}/2000 characters
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex flex-wrap gap-2">
              <span className="text-sm text-muted-foreground">Examples:</span>
              {exampleProducts.map((example, i) => (
                <Button
                  key={i}
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => form.setValue("product_description", example)}
                >
                  Example {i + 1}
                </Button>
              ))}
            </div>

            <FormField
              control={form.control}
              name="sample_size"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Sample Size: {field.value}</FormLabel>
                  <FormControl>
                    <Slider
                      min={5}
                      max={200}
                      step={5}
                      value={[field.value]}
                      onValueChange={(v) => field.onChange(v[0])}
                    />
                  </FormControl>
                  <FormDescription>
                    Number of synthetic respondents (5-200)
                  </FormDescription>
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="use_mock"
              render={({ field }) => (
                <FormItem className="flex items-center justify-between rounded-lg border p-4">
                  <div className="space-y-0.5">
                    <FormLabel>Mock Mode</FormLabel>
                    <FormDescription>
                      Use simulated data (no API key required)
                    </FormDescription>
                  </div>
                  <FormControl>
                    <Switch
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  </FormControl>
                </FormItem>
              )}
            />

            <Card className="bg-muted/50">
              <CardContent className="pt-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Estimated Cost:</span>
                    <p className="font-semibold">
                      {useMock ? "Free (Mock)" : `~$${estimatedCost.toFixed(2)}`}
                    </p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Estimated Time:</span>
                    <p className="font-semibold">~{estimatedTime.toFixed(0)}s</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Running Survey...
                </>
              ) : (
                "Run Survey"
              )}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}

"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
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

const abTestFormSchema = z.object({
  product_a: z
    .string()
    .min(10, "Product description must be at least 10 characters")
    .max(2000, "Product description must be less than 2000 characters"),
  product_b: z
    .string()
    .min(10, "Product description must be at least 10 characters")
    .max(2000, "Product description must be less than 2000 characters"),
  product_a_name: z.string().min(1).max(100),
  product_b_name: z.string().min(1).max(100),
  sample_size: z.number().min(5).max(200),
  use_mock: z.boolean(),
});

type ABTestFormValues = z.infer<typeof abTestFormSchema>;

interface ABTestFormProps {
  onSubmit: (values: ABTestFormValues) => void;
  isLoading?: boolean;
}

export function ABTestForm({ onSubmit, isLoading = false }: ABTestFormProps) {
  const form = useForm<ABTestFormValues>({
    resolver: zodResolver(abTestFormSchema),
    defaultValues: {
      product_a: "",
      product_b: "",
      product_a_name: "Product A",
      product_b_name: "Product B",
      sample_size: 20,
      use_mock: true,
    },
  });

  const sampleSize = form.watch("sample_size");
  const useMock = form.watch("use_mock");

  const estimatedCost = useMock ? 0 : sampleSize * 2 * 0.005;
  const estimatedTime = useMock ? sampleSize * 2 * 0.1 : sampleSize * 2 * 1.5;

  return (
    <Card>
      <CardHeader>
        <CardTitle>A/B Test</CardTitle>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <FormField
                  control={form.control}
                  name="product_a_name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Product A Name</FormLabel>
                      <FormControl>
                        <Input placeholder="Product A" {...field} />
                      </FormControl>
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="product_a"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Product A Description</FormLabel>
                      <FormControl>
                        <Textarea
                          placeholder="Describe product A..."
                          className="min-h-[120px]"
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div className="space-y-4">
                <FormField
                  control={form.control}
                  name="product_b_name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Product B Name</FormLabel>
                      <FormControl>
                        <Input placeholder="Product B" {...field} />
                      </FormControl>
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="product_b"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Product B Description</FormLabel>
                      <FormControl>
                        <Textarea
                          placeholder="Describe product B..."
                          className="min-h-[120px]"
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </div>

            <FormField
              control={form.control}
              name="sample_size"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Sample Size (per product): {field.value}</FormLabel>
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
                    Total respondents: {field.value * 2}
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
                  Running A/B Test...
                </>
              ) : (
                "Run A/B Test"
              )}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}

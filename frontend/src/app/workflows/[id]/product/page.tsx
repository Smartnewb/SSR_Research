"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export default function ProductDescriptionPage() {
  const params = useParams();
  const router = useRouter();
  const workflowId = params.id as string;

  const [formData, setFormData] = useState({
    name: "",
    category: "",
    description: "",
    features: [] as string[],
    price_point: "",
    target_market: "",
  });

  const [featureInput, setFeatureInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [assisting, setAssisting] = useState(false);
  const [dataLoaded, setDataLoaded] = useState(false);

  useEffect(() => {
    loadWorkflowData();
  }, [workflowId]);

  const loadWorkflowData = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/workflows/${workflowId}`
      );
      if (response.ok) {
        const workflow = await response.json();
        if (workflow.product) {
          setFormData({
            name: workflow.product.name || "",
            category: workflow.product.category || "",
            description: workflow.product.description || "",
            features: workflow.product.features || [],
            price_point: workflow.product.price_point || "",
            target_market: workflow.product.target_market || "",
          });
          setDataLoaded(true);
        }
      }
    } catch (error) {
      console.error("Error loading workflow data:", error);
    }
  };

  const handleAddFeature = () => {
    if (featureInput.trim()) {
      setFormData({
        ...formData,
        features: [...formData.features, featureInput.trim()],
      });
      setFeatureInput("");
    }
  };

  const handleRemoveFeature = (index: number) => {
    setFormData({
      ...formData,
      features: formData.features.filter((_, i) => i !== index),
    });
  };

  const handleFillExample = () => {
    setFormData({
      name: "썸타임",
      category: "소개팅 앱",
      description: "지역 대학생 소개팅 앱으로 AI 기반으로 1:1매칭 주변 대학생만 매칭함",
      features: ["AI 매칭", "1:1 소개팅"],
      price_point: "9,900원 / 1회 매칭",
      target_market: "대학생 18~27세",
    });
  };

  const handleGetAIHelp = async () => {
    if (!formData.name || !formData.description) {
      alert("Please enter product name and brief description first");
      return;
    }

    setAssisting(true);
    try {
      const response = await fetch(
        "http://localhost:8000/api/workflows/products/assist?use_mock=true",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            product_name: formData.name,
            brief_description: formData.description,
            target_audience: formData.target_market,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to get AI assistance");
      }

      const data = await response.json();
      setFormData({
        ...formData,
        category: data.category,
        description: data.description,
        features: data.features,
        price_point: data.price_point,
        target_market: data.target_market,
      });
    } catch (error) {
      console.error("Error getting AI help:", error);
      alert("Failed to get AI assistance");
    } finally {
      setAssisting(false);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/workflows/${workflowId}/product`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(formData),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to save product description");
      }

      router.push(`/workflows/${workflowId}/persona`);
    } catch (error) {
      console.error("Error saving product:", error);
      alert("Failed to save product description");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Step 1: Product Description</h1>
        <div className="text-sm text-muted-foreground">Step 1 of 7</div>
      </div>

      {dataLoaded && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <span className="text-green-600 font-semibold">✓ 이전 설정 불러옴</span>
            <span className="text-sm text-green-700">
              이전에 입력했던 제품 정보가 자동으로 채워졌습니다. 수정 후 저장하세요.
            </span>
          </div>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Describe Your Product</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Product Name *</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) =>
                setFormData({ ...formData, name: e.target.value })
              }
              placeholder="e.g., TaskMaster Pro"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="category">Category *</Label>
            <Input
              id="category"
              value={formData.category}
              onChange={(e) =>
                setFormData({ ...formData, category: e.target.value })
              }
              placeholder="e.g., Productivity Software"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description *</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
              placeholder="Describe your product's value proposition and key benefits..."
              rows={4}
            />
          </div>

          <div className="space-y-2">
            <Label>Features</Label>
            <div className="flex gap-2">
              <Input
                value={featureInput}
                onChange={(e) => setFeatureInput(e.target.value)}
                placeholder="Add a feature..."
                onKeyPress={(e) => e.key === "Enter" && handleAddFeature()}
              />
              <Button onClick={handleAddFeature} variant="outline">
                Add
              </Button>
            </div>
            <div className="space-y-1">
              {formData.features.map((feature, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between bg-muted p-2 rounded"
                >
                  <span className="text-sm">{feature}</span>
                  <Button
                    onClick={() => handleRemoveFeature(index)}
                    variant="ghost"
                    size="sm"
                  >
                    Remove
                  </Button>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="price_point">Price Point</Label>
            <Input
              id="price_point"
              value={formData.price_point}
              onChange={(e) =>
                setFormData({ ...formData, price_point: e.target.value })
              }
              placeholder="e.g., $19.99/month"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="target_market">Target Market *</Label>
            <Input
              id="target_market"
              value={formData.target_market}
              onChange={(e) =>
                setFormData({ ...formData, target_market: e.target.value })
              }
              placeholder="e.g., Small business owners aged 30-50"
            />
          </div>

          <div className="flex gap-2 pt-4">
            <Button
              onClick={handleFillExample}
              variant="secondary"
            >
              예시 채우기
            </Button>
            <Button
              onClick={handleGetAIHelp}
              disabled={assisting}
              variant="outline"
              className="flex-1"
            >
              {assisting ? "Getting AI Help..." : "Get AI Help"}
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={loading || !formData.name || !formData.description}
              className="flex-1"
            >
              {loading ? "Saving..." : "Continue to Persona Building"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

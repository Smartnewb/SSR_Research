"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ProductData {
  name: string;
  category: string;
  description: string;
  features: string[];
  price_point: string;
  target_market: string;
}

interface ProductChatPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onApply: (data: ProductData) => void;
  initialData?: Partial<ProductData>;
}

const INITIAL_MESSAGE = `안녕하세요! 제품 설명 작성을 도와드릴게요.

아래 질문에 답변해주시면, 제가 정리된 제품 설명을 만들어 드립니다.

**먼저, 어떤 제품인지 간단히 설명해주세요.**
(예: "대학생을 위한 소개팅 앱을 만들고 있어요")`;

export default function ProductChatPanel({
  open,
  onOpenChange,
  onApply,
  initialData,
}: ProductChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: INITIAL_MESSAGE },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [extractedData, setExtractedData] = useState<ProductData | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 대화 초기화는 별도 함수로 분리 (명시적으로 호출할 때만)
  const resetChat = () => {
    setMessages([{ role: "assistant", content: INITIAL_MESSAGE }]);
    setExtractedData(null);
    setInput("");
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setLoading(true);

    try {
      // 첫 번째 assistant 메시지(INITIAL_MESSAGE)는 UI용이므로 API에서 제외
      const allMessages = [...messages, { role: "user", content: userMessage }];
      const apiMessages = allMessages.slice(1); // 첫 번째 메시지 제외

      const response = await fetch(
        "http://localhost:8000/api/workflows/products/chat",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            messages: apiMessages,
            current_data: initialData,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to get response");
      }

      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.message },
      ]);

      if (data.extracted_data) {
        setExtractedData(data.extracted_data);
      }
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleApply = () => {
    if (extractedData) {
      onApply(extractedData);
      onOpenChange(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[400px] sm:w-[540px] sm:max-w-xl flex flex-col p-0">
        <SheetHeader className="p-6 pb-4 border-b">
          <div className="flex items-center justify-between">
            <div>
              <SheetTitle>AI 제품 설명 도우미</SheetTitle>
              <SheetDescription>
                대화를 통해 제품 설명을 작성해 드립니다
              </SheetDescription>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={resetChat}
              className="text-muted-foreground"
            >
              새 대화
            </Button>
          </div>
        </SheetHeader>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[85%] rounded-lg px-4 py-2 ${
                  message.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted"
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-muted rounded-lg px-4 py-2">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {extractedData && (
          <div className="mx-4 mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <h4 className="font-semibold text-green-800 mb-2">
              정리된 제품 정보
            </h4>
            <div className="text-sm space-y-1 text-green-700">
              <p>
                <strong>제품명:</strong> {extractedData.name}
              </p>
              <p>
                <strong>카테고리:</strong> {extractedData.category}
              </p>
              <p>
                <strong>설명:</strong> {extractedData.description}
              </p>
              <p>
                <strong>기능:</strong> {extractedData.features?.join(", ")}
              </p>
              <p>
                <strong>가격:</strong> {extractedData.price_point}
              </p>
              <p>
                <strong>타겟:</strong> {extractedData.target_market}
              </p>
            </div>
            <Button
              onClick={handleApply}
              className="w-full mt-3 bg-green-600 hover:bg-green-700"
            >
              이 내용으로 적용하기
            </Button>
          </div>
        )}

        <div className="p-4 border-t">
          <div className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="메시지를 입력하세요..."
              disabled={loading}
              className="flex-1"
            />
            <Button onClick={handleSend} disabled={loading || !input.trim()}>
              전송
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}

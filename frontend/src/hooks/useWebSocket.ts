"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { WebSocketProgress, SurveyResponse } from "@/lib/types";

interface UseWebSocketOptions {
  onProgress?: (progress: WebSocketProgress) => void;
  onResult?: (result: SurveyResponse) => void;
  onError?: (error: string) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

interface UseWebSocketReturn {
  connect: (surveyId: string) => void;
  disconnect: () => void;
  isConnected: boolean;
  progress: number;
  currentPersona: number;
  totalPersonas: number;
  status: string;
  error: string | null;
  message: string;
}

const getWebSocketUrl = (surveyId: string): string => {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const wsProtocol = apiUrl.startsWith("https") ? "wss" : "ws";
  const host = apiUrl.replace(/^https?:\/\//, "");
  return `${wsProtocol}://${host}/ws/surveys/${surveyId}`;
};

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    onProgress,
    onResult,
    onError,
    onConnect,
    onDisconnect,
    autoReconnect = false,
    reconnectInterval = 3000,
    maxReconnectAttempts = 3,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const surveyIdRef = useRef<string | null>(null);

  const [isConnected, setIsConnected] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentPersona, setCurrentPersona] = useState(0);
  const [totalPersonas, setTotalPersonas] = useState(0);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState("");

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
    surveyIdRef.current = null;
    reconnectAttemptsRef.current = 0;
  }, []);

  const connect = useCallback(
    (surveyId: string) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        disconnect();
      }

      surveyIdRef.current = surveyId;
      setError(null);
      setProgress(0);
      setCurrentPersona(0);
      setStatus("connecting");

      const url = getWebSocketUrl(surveyId);
      const ws = new WebSocket(url);

      ws.onopen = () => {
        setIsConnected(true);
        setStatus("connected");
        reconnectAttemptsRef.current = 0;
        onConnect?.();
      };

      ws.onmessage = (event) => {
        try {
          const wsMsg: WebSocketProgress = JSON.parse(event.data);

          if (wsMsg.type === "progress") {
            setProgress(wsMsg.progress || 0);
            setCurrentPersona(wsMsg.current_persona || 0);
            setTotalPersonas(wsMsg.total_personas || 0);
            setStatus(wsMsg.status || "running");
            setMessage(wsMsg.message || "Processing...");
            onProgress?.(wsMsg);
          } else if (wsMsg.type === "result") {
            setProgress(100);
            setStatus("completed");
            setMessage("Survey completed!");
            if (wsMsg.data) {
              onResult?.(wsMsg.data);
            }
          } else if (wsMsg.type === "error") {
            setError(wsMsg.error || "Unknown error");
            setStatus("error");
            setMessage(wsMsg.error || "An error occurred");
            onError?.(wsMsg.error || "Unknown error");
          }
        } catch {
          console.error("Failed to parse WebSocket message:", event.data);
        }
      };

      ws.onerror = () => {
        setError("WebSocket connection error");
        setStatus("error");
      };

      ws.onclose = () => {
        setIsConnected(false);
        onDisconnect?.();

        if (
          autoReconnect &&
          surveyIdRef.current &&
          reconnectAttemptsRef.current < maxReconnectAttempts
        ) {
          reconnectAttemptsRef.current += 1;
          setStatus("reconnecting");
          setTimeout(() => {
            if (surveyIdRef.current) {
              connect(surveyIdRef.current);
            }
          }, reconnectInterval);
        }
      };

      wsRef.current = ws;
    },
    [
      disconnect,
      onConnect,
      onDisconnect,
      onProgress,
      onResult,
      onError,
      autoReconnect,
      reconnectInterval,
      maxReconnectAttempts,
    ]
  );

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    connect,
    disconnect,
    isConnected,
    progress,
    currentPersona,
    totalPersonas,
    status,
    error,
    message,
  };
}

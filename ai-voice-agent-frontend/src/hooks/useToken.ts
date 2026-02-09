"use client";

import { useState } from "react";

interface TokenResponse {
  token: string;
  url: string;
}

export function useToken() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getToken = async (
    phoneNumber: string
  ): Promise<TokenResponse | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch("/api/token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phoneNumber }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Failed to get token");
      }

      const data: TokenResponse = await res.json();
      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return { getToken, isLoading, error };
}

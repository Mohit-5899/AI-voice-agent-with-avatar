"use client";

import { useState } from "react";
import { LiveKitRoom } from "@livekit/components-react";
import "@livekit/components-styles";
import { ConnectionState } from "../lib/types";
import { useToken } from "../hooks/useToken";
import { WelcomeView } from "./WelcomeView";
import { SessionView } from "./SessionView";

export function VoiceAgentApp() {
  const [state, setState] = useState<ConnectionState>("welcome");
  const [livekitToken, setLivekitToken] = useState("");
  const [livekitUrl, setLivekitUrl] = useState("");
  const { getToken, isLoading, error } = useToken();

  const handleConnect = async (phoneNumber: string) => {
    setState("connecting");

    const result = await getToken(phoneNumber);
    if (result) {
      setLivekitToken(result.token);
      setLivekitUrl(result.url);
      setState("connected");
    } else {
      setState("welcome");
    }
  };

  const handleDisconnect = () => {
    setLivekitToken("");
    setLivekitUrl("");
    setState("welcome");
  };

  if (state === "welcome" || state === "connecting") {
    return (
      <WelcomeView
        onConnect={handleConnect}
        isLoading={state === "connecting" || isLoading}
        error={error}
      />
    );
  }

  return (
    <LiveKitRoom
      serverUrl={livekitUrl}
      token={livekitToken}
      connect={true}
      audio={true}
      video={false}
      onDisconnected={handleDisconnect}
    >
      <SessionView onDisconnect={handleDisconnect} />
    </LiveKitRoom>
  );
}

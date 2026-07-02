"use client";

import { useEffect, useRef, useState } from "react";
import { Loader2, Send } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import type { AdvisorAskResponse, AdvisorMessage } from "@/lib/types";

const SUGGESTED_QUESTIONS = [
  "What's our biggest revenue problem right now?",
  "What should we build next?",
  "Which experiment has the highest ROI?",
];

export default function AdvisorPage() {
  const [history, setHistory] = useState<AdvisorMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sourcesByMessageId, setSourcesByMessageId] = useState<Record<number, string[]>>({});
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api
      .get<AdvisorMessage[]>("/api/advisor/history")
      .then(setHistory)
      .catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  async function ask(q: string) {
    if (!q.trim() || asking) return;
    setAsking(true);
    setError(null);
    setHistory((prev) => [
      ...prev,
      { id: Date.now(), role: "user", content: q, created_at: new Date().toISOString() },
    ]);
    setQuestion("");
    try {
      const response = await api.post<AdvisorAskResponse>("/api/advisor/ask", { question: q });
      setHistory(response.history);
      const lastMessage = response.history.at(-1);
      if (lastMessage) {
        setSourcesByMessageId((prev) => ({ ...prev, [lastMessage.id]: response.sources }));
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setAsking(false);
    }
  }

  return (
    <div className="flex h-screen flex-col">
      <PageHeader
        title="AI Founder Advisor"
        description="Retrieval-grounded: every answer is drawn from your live funnel, revenue, experiment, and Growth Twin data."
      />
      <ScrollArea className="flex-1 px-8 py-6">
        <div className="mx-auto max-w-2xl space-y-4">
          {history.length === 0 && (
            <div className="flex flex-wrap gap-2">
              {SUGGESTED_QUESTIONS.map((q) => (
                <Button key={q} variant="outline" size="sm" onClick={() => ask(q)}>
                  {q}
                </Button>
              ))}
            </div>
          )}
          {history.map((message) => (
            <div
              key={message.id}
              className={cn("flex flex-col", message.role === "user" ? "items-end" : "items-start")}
            >
              <div
                className={cn(
                  "max-w-[80%] whitespace-pre-wrap rounded-lg px-4 py-2 text-sm",
                  message.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-foreground"
                )}
              >
                {message.content}
              </div>
              {sourcesByMessageId[message.id] && sourcesByMessageId[message.id].length > 0 && (
                <div className="mt-1.5 flex max-w-[80%] flex-wrap gap-1">
                  <span className="text-xs text-muted-foreground">Sources:</span>
                  {sourcesByMessageId[message.id].map((source) => (
                    <Badge key={source} variant="outline" className="text-xs font-normal">
                      {source}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          ))}
          {error && <p className="text-sm text-destructive">{error}</p>}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>
      <div className="border-t p-4">
        <form
          className="mx-auto flex max-w-2xl items-end gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            ask(question);
          }}
        >
          <Textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask your AI advisor anything about growth or revenue..."
            rows={1}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                ask(question);
              }
            }}
          />
          <Button type="submit" disabled={asking || !question.trim()}>
            {asking ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
          </Button>
        </form>
      </div>
    </div>
  );
}

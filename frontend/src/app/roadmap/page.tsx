"use client";

import { useEffect, useMemo, useState } from "react";
import { Loader2, Sparkles } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/utils";
import type { RoadmapItem } from "@/lib/types";

function nextQuarters(count: number): string[] {
  const now = new Date();
  const year = now.getFullYear();
  const currentQuarter = Math.floor(now.getMonth() / 3) + 1;
  return Array.from({ length: count }, (_, i) => {
    const total = currentQuarter + i;
    const q = ((total - 1) % 4) + 1;
    const y = year + Math.floor((total - 1) / 4);
    return `Q${q} ${y}`;
  });
}

const EFFORT_VARIANT: Record<string, "default" | "secondary" | "outline"> = {
  small: "secondary",
  medium: "default",
  large: "outline",
};

export default function RoadmapPage() {
  const quarters = useMemo(() => nextQuarters(4), []);
  const [quarter, setQuarter] = useState(quarters[0]);
  const [items, setItems] = useState<RoadmapItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    api
      .get<RoadmapItem[]>("/api/roadmap")
      .then(setItems)
      .catch((e) => setError(e.message));
  }, []);

  async function generate() {
    setGenerating(true);
    try {
      const generated = await api.post<RoadmapItem[]>("/api/roadmap/generate", { quarter });
      setItems((prev) => [...generated, ...(prev ?? [])]);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="AI Product Roadmap Generator"
        description="Quarterly roadmap ranked by revenue impact, effort, and confidence."
        action={
          <div className="flex items-center gap-2">
            <Select value={quarter} onValueChange={(v) => v && setQuarter(v)}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {quarters.map((q) => (
                  <SelectItem key={q} value={q}>
                    {q}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button onClick={generate} disabled={generating}>
              {generating ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
              Generate Roadmap
            </Button>
          </div>
        }
      />
      <div className="space-y-4 p-8">
        {error && (
          <p className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
            Couldn&apos;t reach the API ({error}).
          </p>
        )}
        {!items && !error && <Skeleton className="h-40 w-full" />}
        {items?.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No roadmap items yet. Pick a quarter and click &ldquo;Generate Roadmap&rdquo;.
          </p>
        )}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {items?.map((item) => (
            <Card key={item.id}>
              <CardHeader>
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-base">{item.title}</CardTitle>
                  <Badge variant="outline">{item.quarter}</Badge>
                </div>
                <CardDescription>{item.description}</CardDescription>
              </CardHeader>
              <CardContent className="flex items-center gap-3 text-sm">
                <span className="font-medium text-emerald-600 dark:text-emerald-400">
                  +{formatCurrency(item.revenue_impact)}/mo
                </span>
                <Badge variant={EFFORT_VARIANT[item.effort] ?? "default"}>{item.effort} effort</Badge>
                <span className="text-muted-foreground">
                  {formatPercent(item.confidence_score)} confidence
                </span>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

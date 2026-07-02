"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, FlaskConical, Loader2, Sparkles, XCircle } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/utils";
import type { Experiment } from "@/lib/types";

export default function ExperimentsPage() {
  const [experiments, setExperiments] = useState<Experiment[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [runningId, setRunningId] = useState<number | null>(null);

  function load() {
    api
      .get<Experiment[]>("/api/experiments")
      .then(setExperiments)
      .catch((e) => setError(e.message));
  }

  useEffect(load, []);

  async function generate() {
    setGenerating(true);
    try {
      const experiment = await api.post<Experiment>("/api/experiments/generate", {});
      setExperiments((prev) => [experiment, ...(prev ?? [])]);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setGenerating(false);
    }
  }

  async function runExperiment(id: number) {
    setRunningId(id);
    try {
      const updated = await api.post<Experiment>(`/api/experiments/${id}/run`, {
        sample_size_per_arm: 1000,
      });
      setExperiments((prev) => (prev ?? []).map((e) => (e.id === id ? updated : e)));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setRunningId(null);
    }
  }

  return (
    <div>
      <PageHeader
        title="AI Experiment Generator"
        description="LLM-generated hypotheses, measured with a real randomized-trial simulation (z-test, confidence interval, p-value)."
        action={
          <Button onClick={generate} disabled={generating}>
            {generating ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
            Generate Experiment
          </Button>
        }
      />
      <div className="space-y-4 p-8">
        {error && (
          <p className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
            Couldn&apos;t reach the API ({error}).
          </p>
        )}
        {!experiments && !error && <Skeleton className="h-40 w-full" />}
        {experiments?.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No experiments yet. Click &ldquo;Generate Experiment&rdquo; to get an AI-suggested A/B test.
          </p>
        )}
        {experiments?.map((exp) => (
          <Card key={exp.id}>
            <CardHeader>
              <div className="flex items-start justify-between gap-2">
                <CardTitle className="text-base">Hypothesis</CardTitle>
                <Badge variant="outline">confidence {formatPercent(exp.confidence_score)}</Badge>
              </div>
              <CardDescription>{exp.hypothesis}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div className="rounded-md border p-3">
                  <div className="text-xs font-medium text-muted-foreground">Current</div>
                  <div className="mt-1 text-sm">{exp.current_variant}</div>
                </div>
                <div className="rounded-md border border-primary/40 bg-primary/5 p-3">
                  <div className="text-xs font-medium text-primary">Suggested</div>
                  <div className="mt-1 text-sm">{exp.suggested_variant}</div>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-4 text-sm">
                <span className="font-medium text-emerald-600 dark:text-emerald-400">
                  +{exp.expected_uplift_pct}% hypothesized uplift
                </span>
                <span className="font-medium text-emerald-600 dark:text-emerald-400">
                  +{formatCurrency(exp.expected_revenue_impact)}/mo hypothesized
                </span>
                <Badge variant="secondary">{exp.status}</Badge>
              </div>

              {exp.status === "suggested" && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => runExperiment(exp.id)}
                  disabled={runningId === exp.id}
                >
                  {runningId === exp.id ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <FlaskConical className="size-4" />
                  )}
                  Run Simulated Trial (1,000 users/arm)
                </Button>
              )}

              {exp.status === "completed" && (
                <>
                  <Separator />
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      {exp.result_is_significant ? (
                        <Badge className="gap-1 bg-emerald-600 hover:bg-emerald-600">
                          <CheckCircle2 className="size-3" /> Statistically significant
                        </Badge>
                      ) : (
                        <Badge variant="destructive" className="gap-1">
                          <XCircle className="size-3" /> Not statistically significant
                        </Badge>
                      )}
                      <span className="text-xs text-muted-foreground">
                        p = {exp.result_p_value} · n = {exp.result_sample_size_per_arm}/arm
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                      <ResultStat label="Control" value={formatPercent(exp.result_control_rate ?? 0)} />
                      <ResultStat label="Variant" value={formatPercent(exp.result_variant_rate ?? 0)} />
                      <ResultStat
                        label="Observed uplift"
                        value={`${exp.result_observed_uplift_pct?.toFixed(1)}%`}
                        tone={
                          (exp.result_observed_uplift_pct ?? 0) >= 0 ? "positive" : "negative"
                        }
                      />
                      <ResultStat
                        label="95% CI (diff)"
                        value={`${((exp.result_ci_low ?? 0) * 100).toFixed(1)}, ${((exp.result_ci_high ?? 0) * 100).toFixed(1)}`}
                      />
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function ResultStat({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: string;
  tone?: "default" | "positive" | "negative";
}) {
  return (
    <div className="rounded-md border p-2">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div
        className={
          tone === "positive"
            ? "text-sm font-semibold text-emerald-600 dark:text-emerald-400"
            : tone === "negative"
              ? "text-sm font-semibold text-red-600 dark:text-red-400"
              : "text-sm font-semibold"
        }
      >
        {value}
      </div>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from "recharts";
import { AlertTriangle, Loader2, RefreshCw } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { MetricCard } from "@/components/metric-card";
import { api } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/utils";
import type { GrowthTwinSnapshot } from "@/lib/types";

export default function GrowthTwinPage() {
  const [snapshots, setSnapshots] = useState<GrowthTwinSnapshot[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  function load() {
    api
      .get<GrowthTwinSnapshot[]>("/api/growth-twin/snapshots")
      .then((data) => setSnapshots([...data].reverse()))
      .catch((e) => setError(e.message));
  }

  useEffect(load, []);

  async function refresh() {
    setRefreshing(true);
    try {
      const snapshot = await api.post<GrowthTwinSnapshot>("/api/growth-twin/refresh");
      setSnapshots((prev) => [...(prev ?? []), snapshot]);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setRefreshing(false);
    }
  }

  const latest = snapshots?.at(-1);
  const chartData = snapshots?.map((s) => ({
    date: new Date(s.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
    mrr: s.predicted_mrr,
  }));

  return (
    <div>
      <PageHeader
        title="Growth Twin Engine"
        description="A continuously-updated digital twin predicting where your business is headed."
        action={
          <Button onClick={refresh} disabled={refreshing}>
            {refreshing ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
            Refresh Prediction
          </Button>
        }
      />
      <div className="space-y-6 p-8">
        {error && (
          <p className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
            Couldn&apos;t reach the API ({error}).
          </p>
        )}
        {!snapshots && !error && <Skeleton className="h-80 w-full" />}
        {snapshots?.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No predictions yet. Click &ldquo;Refresh Prediction&rdquo; to run the Growth Twin Engine.
          </p>
        )}
        {latest?.insufficient_data && (
          <p className="flex items-center gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-700 dark:text-amber-400">
            <AlertTriangle className="size-4 shrink-0" />
            Not enough historical data to train a reliable model yet — predictions below fall back
            to observed rates.
          </p>
        )}
        {latest && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard label="Predicted MRR" value={formatCurrency(latest.predicted_mrr)} />
            <MetricCard
              label="Predicted Activation Rate"
              value={formatPercent(latest.predicted_activation_rate)}
            />
            <MetricCard
              label="Predicted Paid Conversion"
              value={formatPercent(latest.predicted_paid_conversion_rate)}
            />
            <MetricCard
              label="Predicted Churn Rate"
              value={formatPercent(latest.predicted_churn_rate)}
              tone="negative"
            />
          </div>
        )}
        {latest && !latest.insufficient_data && (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <ModelCard
              title="Conversion Model"
              description="RandomForestClassifier predicting trial → paid probability"
              auc={latest.conversion_model_auc}
              accuracy={latest.conversion_model_accuracy}
              featureImportance={latest.conversion_feature_importance}
            />
            <ModelCard
              title="Churn Model"
              description="LogisticRegression predicting paying-customer churn probability"
              auc={latest.churn_model_auc}
              accuracy={latest.churn_model_accuracy}
              featureImportance={latest.churn_feature_importance}
            />
          </div>
        )}
        {snapshots && snapshots.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Predicted MRR Trend</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="mrr" stroke="var(--primary)" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

function ModelCard({
  title,
  description,
  auc,
  accuracy,
  featureImportance,
}: {
  title: string;
  description: string;
  auc: number | null;
  accuracy: number | null;
  featureImportance: Record<string, number>;
}) {
  const features = Object.entries(featureImportance).sort(([, a], [, b]) => b - a);
  const maxImportance = features[0]?.[1] ?? 1;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-6 text-sm">
          <div>
            <div className="text-xs text-muted-foreground">AUC</div>
            <div className="text-lg font-semibold">{auc !== null ? auc.toFixed(3) : "—"}</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground">Accuracy</div>
            <div className="text-lg font-semibold">{accuracy !== null ? formatPercent(accuracy) : "—"}</div>
          </div>
        </div>
        <div className="space-y-2">
          <div className="text-xs font-medium text-muted-foreground">Top feature importance</div>
          {features.map(([name, value]) => (
            <div key={name} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="font-mono">{name}</span>
                <span className="text-muted-foreground">{(value * 100).toFixed(1)}%</span>
              </div>
              <Progress value={(value / maxImportance) * 100} className="h-1.5" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

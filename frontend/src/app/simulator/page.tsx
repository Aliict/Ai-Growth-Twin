"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Separator } from "@/components/ui/separator";
import { api } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/utils";
import type { SimulationRequest, SimulationResult } from "@/lib/types";

export default function SimulatorPage() {
  const [activationDelta, setActivationDelta] = useState(10);
  const [conversionDelta, setConversionDelta] = useState(0);
  const [churnDelta, setChurnDelta] = useState(0);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const request: SimulationRequest = {
      activation_rate_delta_pct: activationDelta,
      paid_conversion_rate_delta_pct: conversionDelta,
      churn_rate_delta_pct: churnDelta,
    };
    setLoading(true);
    const timeout = setTimeout(() => {
      api
        .post<SimulationResult>("/api/simulator", request)
        .then(setResult)
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    }, 250);
    return () => clearTimeout(timeout);
  }, [activationDelta, conversionDelta, churnDelta]);

  return (
    <div>
      <PageHeader
        title="Revenue Simulator"
        description="Predict how changes in activation, conversion, and churn move your MRR."
      />
      <div className="grid grid-cols-1 gap-6 p-8 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>What if...</CardTitle>
          </CardHeader>
          <CardContent className="space-y-8">
            <SliderControl
              label="Activation rate"
              value={activationDelta}
              onChange={setActivationDelta}
            />
            <SliderControl
              label="Paid conversion rate"
              value={conversionDelta}
              onChange={setConversionDelta}
            />
            <SliderControl
              label="Churn rate"
              value={churnDelta}
              onChange={setChurnDelta}
              invert
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Projected Impact</CardTitle>
            {loading && <Loader2 className="size-4 animate-spin text-muted-foreground" />}
          </CardHeader>
          <CardContent>
            {error && <p className="text-sm text-destructive">{error}</p>}
            {result && (
              <div className="space-y-4">
                <div>
                  <div className="text-sm text-muted-foreground">Projected MRR</div>
                  <div className="text-3xl font-bold">{formatCurrency(result.projected_mrr)}</div>
                  <div
                    className={
                      result.mrr_delta >= 0
                        ? "text-sm font-medium text-emerald-600 dark:text-emerald-400"
                        : "text-sm font-medium text-red-600 dark:text-red-400"
                    }
                  >
                    {result.mrr_delta >= 0 ? "+" : ""}
                    {formatCurrency(result.mrr_delta)} vs. baseline {formatCurrency(result.baseline_mrr)}
                  </div>
                </div>
                <Separator />
                <MetricRow
                  label="Activation rate"
                  baseline={result.baseline_activation_rate}
                  projected={result.projected_activation_rate}
                />
                <MetricRow
                  label="Paid conversion rate"
                  baseline={result.baseline_paid_conversion_rate}
                  projected={result.projected_paid_conversion_rate}
                />
                <MetricRow
                  label="Churn rate"
                  baseline={result.baseline_churn_rate}
                  projected={result.projected_churn_rate}
                />
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function SliderControl({
  label,
  value,
  onChange,
  invert = false,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  invert?: boolean;
}) {
  const positive = invert ? value <= 0 : value >= 0;
  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-sm">
        <span className="font-medium">{label}</span>
        <span className={positive ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400"}>
          {value > 0 ? "+" : ""}
          {value}%
        </span>
      </div>
      <Slider
        min={-50}
        max={50}
        step={1}
        value={value}
        onValueChange={(v) => onChange(v as number)}
      />
    </div>
  );
}

function MetricRow({
  label,
  baseline,
  projected,
}: {
  label: string;
  baseline: number;
  projected: number;
}) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span>
        {formatPercent(baseline)} <span className="text-muted-foreground">→</span>{" "}
        <span className="font-semibold">{formatPercent(projected)}</span>
      </span>
    </div>
  );
}

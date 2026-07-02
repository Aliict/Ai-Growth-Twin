"use client";

import { useEffect, useState } from "react";
import { Droplets, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import type { RevenueLeakSummary } from "@/lib/types";

export default function RevenueLeaksPage() {
  const [data, setData] = useState<RevenueLeakSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [detecting, setDetecting] = useState(false);

  function load() {
    api
      .get<RevenueLeakSummary>("/api/revenue-leaks")
      .then(setData)
      .catch((e) => setError(e.message));
  }

  useEffect(load, []);

  async function detect() {
    setDetecting(true);
    try {
      const result = await api.post<RevenueLeakSummary>("/api/revenue-leaks/detect");
      setData(result);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setDetecting(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Revenue Leak Detector"
        description="Where onboarding friction and activation failures are costing you money."
        action={
          <Button onClick={detect} disabled={detecting}>
            {detecting && <Loader2 className="size-4 animate-spin" />}
            Re-run Detection
          </Button>
        }
      />
      <div className="space-y-6 p-8">
        {error && (
          <p className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
            Couldn&apos;t reach the API ({error}).
          </p>
        )}
        {!data && !error && <Skeleton className="h-40 w-full" />}
        {data && (
          <>
            <Card className="border-destructive/30 bg-destructive/5">
              <CardHeader className="flex flex-row items-center gap-3">
                <Droplets className="size-5 text-destructive" />
                <div>
                  <CardTitle>Total Monthly Leakage</CardTitle>
                  <CardDescription>Estimated lost revenue across all detected leaks</CardDescription>
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-destructive">
                  {formatCurrency(data.total_monthly_leakage)}/month
                </div>
              </CardContent>
            </Card>

            {data.leaks.length === 0 && (
              <p className="text-sm text-muted-foreground">
                No leaks detected yet. Click &ldquo;Re-run Detection&rdquo; to analyze the current funnel.
              </p>
            )}

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              {data.leaks.map((leak) => (
                <Card key={leak.id}>
                  <CardHeader>
                    <div className="flex items-start justify-between gap-2">
                      <CardTitle className="text-base">{leak.title}</CardTitle>
                      <Badge variant="secondary">{leak.category.replaceAll("_", " ")}</Badge>
                    </div>
                    <CardDescription>{leak.description}</CardDescription>
                  </CardHeader>
                  <CardContent className="flex items-center justify-between">
                    <Badge variant="outline">{leak.status}</Badge>
                    <span className="font-semibold text-destructive">
                      -{formatCurrency(leak.monthly_impact)}/mo
                    </span>
                  </CardContent>
                </Card>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

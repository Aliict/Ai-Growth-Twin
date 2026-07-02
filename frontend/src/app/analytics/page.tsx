"use client";

import { useEffect, useState } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { api } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/utils";
import type { CohortRow, RetentionPoint, RevenueForecast, RevenueMetrics } from "@/lib/types";

export default function AnalyticsPage() {
  const [cohorts, setCohorts] = useState<CohortRow[] | null>(null);
  const [retention, setRetention] = useState<RetentionPoint[] | null>(null);
  const [forecast, setForecast] = useState<RevenueForecast | null>(null);
  const [segments, setSegments] = useState<RevenueMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.get<CohortRow[]>("/api/analytics/cohorts"),
      api.get<RetentionPoint[]>("/api/analytics/retention"),
      api.get<RevenueForecast>("/api/analytics/forecast"),
      api.get<RevenueMetrics>("/api/revenue/segments"),
    ])
      .then(([c, r, f, s]) => {
        setCohorts(c);
        setRetention(r);
        setForecast(f);
        setSegments(s);
      })
      .catch((e) => setError(e.message));
  }, []);

  const forecastChartData = forecast
    ? [
        ...forecast.history.map((p) => ({ date: p.date, mrr: p.mrr })),
        ...forecast.forecast.map((p) => ({
          date: p.date,
          predicted_mrr: p.predicted_mrr,
          band: [p.confidence_low, p.confidence_high] as [number, number],
        })),
      ]
    : [];

  return (
    <div>
      <PageHeader
        title="Analytics"
        description="Cohort retention, acquisition-channel performance, and a real linear-regression MRR forecast."
      />
      <div className="space-y-6 p-8">
        {error && (
          <p className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
            Couldn&apos;t reach the API ({error}).
          </p>
        )}
        {!forecast && !error && <Skeleton className="h-72 w-full" />}

        {forecast && (
          <Card>
            <CardHeader>
              <CardTitle>MRR Forecast</CardTitle>
              <CardDescription>
                LinearRegression over {forecast.history.length} weeks of reconstructed history
                (R² = {forecast.r_squared ?? "—"}), projected {forecast.forecast.length} weeks ahead.
                Trend: {forecast.trend_per_week >= 0 ? "+" : ""}
                {formatCurrency(forecast.trend_per_week)}/week.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={280}>
                <ComposedChart data={forecastChartData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Area
                    dataKey="band"
                    stroke="none"
                    fill="var(--primary)"
                    fillOpacity={0.12}
                    connectNulls
                  />
                  <Line dataKey="mrr" stroke="var(--primary)" strokeWidth={2} dot={false} name="Actual MRR" />
                  <Line
                    dataKey="predicted_mrr"
                    stroke="var(--primary)"
                    strokeDasharray="5 4"
                    strokeWidth={2}
                    dot={false}
                    name="Forecast"
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Retention Curve</CardTitle>
              <CardDescription>% of paying customers still active N months after converting</CardDescription>
            </CardHeader>
            <CardContent>
              {!retention && <Skeleton className="h-48 w-full" />}
              {retention && (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Month</TableHead>
                      <TableHead className="text-right">Retained</TableHead>
                      <TableHead className="text-right">Customers</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {retention.map((point) => (
                      <TableRow key={point.month}>
                        <TableCell>Month {point.month}</TableCell>
                        <TableCell className="text-right">
                          {point.retained_pct !== null ? formatPercent(point.retained_pct) : "not enough data"}
                        </TableCell>
                        <TableCell className="text-right">{point.eligible_customers}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Signup Cohorts</CardTitle>
              <CardDescription>Conversion and current retention by signup month</CardDescription>
            </CardHeader>
            <CardContent>
              {!cohorts && <Skeleton className="h-48 w-full" />}
              {cohorts && (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Cohort</TableHead>
                      <TableHead className="text-right">Signups</TableHead>
                      <TableHead className="text-right">Converted</TableHead>
                      <TableHead className="text-right">Still active</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {cohorts.map((row) => (
                      <TableRow key={row.cohort}>
                        <TableCell className="font-medium">{row.cohort}</TableCell>
                        <TableCell className="text-right">{row.signups}</TableCell>
                        <TableCell className="text-right">
                          {row.converted} ({formatPercent(row.conversion_rate)})
                        </TableCell>
                        <TableCell className="text-right">
                          {row.still_active}
                          {row.current_retention_rate !== null && (
                            <span className="text-muted-foreground"> ({formatPercent(row.current_retention_rate)})</span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Acquisition Channels</CardTitle>
              <CardDescription>Conversion rate and blended CAC by channel</CardDescription>
            </CardHeader>
            <CardContent>
              {!segments && <Skeleton className="h-48 w-full" />}
              {segments && (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Channel</TableHead>
                      <TableHead className="text-right">Signups</TableHead>
                      <TableHead className="text-right">Conv. rate</TableHead>
                      <TableHead className="text-right">MRR</TableHead>
                      <TableHead className="text-right">CAC</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {segments.channel_breakdown.map((row) => (
                      <TableRow key={row.channel}>
                        <TableCell className="font-medium capitalize">{row.channel.replace("_", " ")}</TableCell>
                        <TableCell className="text-right">{row.signups}</TableCell>
                        <TableCell className="text-right">{formatPercent(row.conversion_rate)}</TableCell>
                        <TableCell className="text-right">{formatCurrency(row.mrr)}</TableCell>
                        <TableCell className="text-right">
                          {row.cac !== null ? formatCurrency(row.cac) : "—"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Plan Mix</CardTitle>
              <CardDescription>Customers and MRR by plan tier</CardDescription>
            </CardHeader>
            <CardContent>
              {!segments && <Skeleton className="h-48 w-full" />}
              {segments && (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Plan</TableHead>
                      <TableHead className="text-right">Customers</TableHead>
                      <TableHead className="text-right">Share</TableHead>
                      <TableHead className="text-right">MRR</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {segments.plan_breakdown.map((row) => (
                      <TableRow key={row.plan}>
                        <TableCell className="font-medium capitalize">{row.plan}</TableCell>
                        <TableCell className="text-right">{row.customers}</TableCell>
                        <TableCell className="text-right">{formatPercent(row.share_of_customers)}</TableCell>
                        <TableCell className="text-right">{formatCurrency(row.mrr)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

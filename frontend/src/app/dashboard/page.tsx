"use client";

import { useEffect, useState } from "react";
import {
  DollarSign,
  TrendingUp,
  Users,
  Gauge,
  CreditCard,
  Droplets,
  ArrowUpRight,
  Wallet,
  Timer,
  Scale,
} from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { MetricCard } from "@/components/metric-card";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/utils";
import type { ExecutiveDashboard } from "@/lib/types";

export default function DashboardPage() {
  const [data, setData] = useState<ExecutiveDashboard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<ExecutiveDashboard>("/api/dashboard")
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div>
      <PageHeader
        title="Executive Dashboard"
        description="Live revenue and growth health for your SaaS business."
      />
      <div className="p-8">
        {error && (
          <p className="mb-4 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
            Couldn&apos;t reach the API ({error}). Is the backend running and seeded?
          </p>
        )}
        {!data && !error && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 10 }).map((_, i) => (
              <Skeleton key={i} className="h-28 w-full" />
            ))}
          </div>
        )}
        {data && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard label="MRR" value={formatCurrency(data.mrr)} icon={DollarSign} />
            <MetricCard label="ARR" value={formatCurrency(data.arr)} icon={TrendingUp} />
            <MetricCard label="Trial Users" value={data.trial_users.toLocaleString()} icon={Users} />
            <MetricCard
              label="Activation Rate"
              value={formatPercent(data.activation_rate)}
              icon={Gauge}
            />
            <MetricCard
              label="Paid Conversion Rate"
              value={formatPercent(data.paid_conversion_rate)}
              icon={CreditCard}
            />
            <MetricCard
              label="Revenue Leakage"
              value={formatCurrency(data.revenue_leakage)}
              icon={Droplets}
              tone="negative"
              hint="per month, estimated"
            />
            <MetricCard
              label="Expansion Opportunity"
              value={formatCurrency(data.expansion_opportunity)}
              icon={ArrowUpRight}
              tone="positive"
              hint="per month, estimated"
            />
            <MetricCard label="LTV" value={formatCurrency(data.ltv)} icon={Wallet} hint={`ARPU ${formatCurrency(data.arpu)}/mo`} />
            <MetricCard
              label="CAC"
              value={data.cac !== null ? formatCurrency(data.cac) : "—"}
              icon={Timer}
              hint={
                data.payback_period_months !== null
                  ? `${data.payback_period_months.toFixed(1)}mo payback`
                  : "no channel spend data yet"
              }
            />
            <MetricCard
              label="LTV : CAC"
              value={data.ltv_cac_ratio !== null ? `${data.ltv_cac_ratio.toFixed(1)}x` : "—"}
              icon={Scale}
              tone={data.ltv_cac_ratio !== null && data.ltv_cac_ratio >= 3 ? "positive" : "negative"}
              hint="healthy SaaS benchmark is ≥ 3x"
            />
          </div>
        )}
      </div>
    </div>
  );
}

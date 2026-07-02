"use client";

import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
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
import type { FunnelAnalysis } from "@/lib/types";

const STAGE_LABELS: Record<string, string> = {
  signup: "Signup",
  activation: "Activation",
  project_creation: "Project Creation",
  team_invite: "Team Invite",
  trial_usage: "Trial Usage",
  paid: "Paid",
};

export default function FunnelPage() {
  const [data, setData] = useState<FunnelAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<FunnelAnalysis>("/api/funnel")
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);

  const chartData = data?.stages.map((s) => ({
    name: STAGE_LABELS[s.stage] ?? s.stage,
    users: s.users,
  }));

  return (
    <div>
      <PageHeader
        title="Funnel Analyzer"
        description="Signup → Activation → Project Creation → Team Invite → Trial Usage → Paid"
      />
      <div className="space-y-6 p-8">
        {error && (
          <p className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
            Couldn&apos;t reach the API ({error}).
          </p>
        )}
        {!data && !error && <Skeleton className="h-80 w-full" />}
        {data && (
          <>
            <Card>
              <CardContent className="pt-6">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                    <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="users" fill="var(--primary)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Stage</TableHead>
                      <TableHead className="text-right">Users</TableHead>
                      <TableHead className="text-right">Conversion Rate</TableHead>
                      <TableHead className="text-right">Dropoff Rate</TableHead>
                      <TableHead className="text-right">Revenue Impact</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.stages.map((stage) => (
                      <TableRow key={stage.stage}>
                        <TableCell className="font-medium">
                          {STAGE_LABELS[stage.stage] ?? stage.stage}
                        </TableCell>
                        <TableCell className="text-right">{stage.users.toLocaleString()}</TableCell>
                        <TableCell className="text-right">{formatPercent(stage.conversion_rate)}</TableCell>
                        <TableCell className="text-right">{formatPercent(stage.dropoff_rate)}</TableCell>
                        <TableCell className="text-right">{formatCurrency(stage.revenue_impact)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}

export interface ExecutiveDashboard {
  mrr: number;
  arr: number;
  trial_users: number;
  activation_rate: number;
  paid_conversion_rate: number;
  revenue_leakage: number;
  expansion_opportunity: number;
  arpu: number;
  ltv: number;
  cac: number | null;
  payback_period_months: number | null;
  ltv_cac_ratio: number | null;
}

export interface FunnelStage {
  stage: string;
  users: number;
  conversion_rate: number;
  dropoff_rate: number;
  revenue_impact: number;
}

export interface FunnelAnalysis {
  stages: FunnelStage[];
  overall_conversion_rate: number;
}

export interface RevenueLeak {
  id: number;
  title: string;
  stage: string;
  description: string;
  category: string;
  monthly_impact: number;
  status: string;
  detected_at: string;
}

export interface RevenueLeakSummary {
  total_monthly_leakage: number;
  leaks: RevenueLeak[];
}

export interface Experiment {
  id: number;
  hypothesis: string;
  current_variant: string;
  suggested_variant: string;
  expected_uplift_pct: number;
  expected_revenue_impact: number;
  confidence_score: number;
  status: string;
  created_at: string;
  result_sample_size_per_arm: number | null;
  result_control_conversions: number | null;
  result_control_rate: number | null;
  result_variant_conversions: number | null;
  result_variant_rate: number | null;
  result_observed_uplift_pct: number | null;
  result_p_value: number | null;
  result_is_significant: boolean | null;
  result_ci_low: number | null;
  result_ci_high: number | null;
  completed_at: string | null;
}

export interface SimulationRequest {
  activation_rate_delta_pct: number;
  paid_conversion_rate_delta_pct: number;
  churn_rate_delta_pct: number;
}

export interface SimulationResult {
  baseline_mrr: number;
  projected_mrr: number;
  mrr_delta: number;
  baseline_activation_rate: number;
  projected_activation_rate: number;
  baseline_paid_conversion_rate: number;
  projected_paid_conversion_rate: number;
  baseline_churn_rate: number;
  projected_churn_rate: number;
}

export interface AdvisorMessage {
  id: number;
  role: string;
  content: string;
  created_at: string;
}

export interface AdvisorAskResponse {
  answer: string;
  sources: string[];
  history: AdvisorMessage[];
}

export interface RoadmapItem {
  id: number;
  quarter: string;
  title: string;
  description: string;
  revenue_impact: number;
  effort: string;
  confidence_score: number;
  created_at: string;
}

export interface GrowthTwinSnapshot {
  id: number;
  predicted_mrr: number;
  predicted_churn_rate: number;
  predicted_activation_rate: number;
  predicted_expansion_mrr: number;
  predicted_paid_conversion_rate: number;
  conversion_model_auc: number | null;
  conversion_model_accuracy: number | null;
  churn_model_auc: number | null;
  churn_model_accuracy: number | null;
  conversion_feature_importance: Record<string, number>;
  churn_feature_importance: Record<string, number>;
  insufficient_data: boolean;
  created_at: string;
}

export interface PlanBreakdown {
  plan: string;
  customers: number;
  mrr: number;
  arpu: number;
  share_of_customers: number;
}

export interface ChannelBreakdown {
  channel: string;
  signups: number;
  conversions: number;
  conversion_rate: number;
  mrr: number;
  cac: number | null;
}

export interface RevenueMetrics {
  arpu: number;
  monthly_churn_rate: number;
  customer_lifetime_months: number;
  ltv: number;
  cac: number | null;
  payback_period_months: number | null;
  ltv_cac_ratio: number | null;
  plan_breakdown: PlanBreakdown[];
  channel_breakdown: ChannelBreakdown[];
}

export interface CohortRow {
  cohort: string;
  signups: number;
  converted: number;
  conversion_rate: number;
  still_active: number;
  current_retention_rate: number | null;
}

export interface RetentionPoint {
  month: number;
  retained_pct: number | null;
  eligible_customers: number;
}

export interface MrrHistoryPoint {
  date: string;
  mrr: number;
}

export interface MrrForecastPoint {
  date: string;
  predicted_mrr: number;
  confidence_low: number;
  confidence_high: number;
}

export interface RevenueForecast {
  history: MrrHistoryPoint[];
  forecast: MrrForecastPoint[];
  trend_per_week: number;
  r_squared: number | null;
}

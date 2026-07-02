"""Lightweight retrieval for the AI Founder Advisor.

LangChain isn't in this project's dependencies, and pulling it in just to
wrap a TF-IDF lookup would be a heavier dependency than the problem
warrants. Since scikit-learn is already required for the Growth Twin models,
its TfidfVectorizer + cosine_similarity give a real (if simple) retrieval
step: business data is chunked into documents, ranked against the question,
and only the top-k are put in the LLM's context — the model reasons over
retrieved facts instead of being handed the entire database as one blob.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.experiment import Experiment
from app.models.growth_twin_snapshot import GrowthTwinSnapshot
from app.models.revenue_leak import RevenueLeak
from app.services import growth_analytics
from app.services.analytics import compute_dashboard_metrics, compute_funnel
from app.services.revenue import compute_revenue_metrics


def build_knowledge_base(db: Session, company_id: int) -> list[dict]:
    documents: list[dict] = []

    metrics = compute_dashboard_metrics(db, company_id)
    documents.append(
        {
            "title": "Executive summary",
            "text": (
                f"MRR is ${metrics['mrr']:.0f}/mo (${metrics['arr']:.0f}/yr ARR). "
                f"Activation rate is {metrics['activation_rate']:.1%}, paid conversion rate is "
                f"{metrics['paid_conversion_rate']:.1%}. Estimated revenue leakage is "
                f"${metrics['revenue_leakage']:.0f}/mo. Expansion opportunity is "
                f"${metrics['expansion_opportunity']:.0f}/mo. ARPU is ${metrics['arpu']:.0f}, LTV is "
                f"${metrics['ltv']:.0f}, CAC is "
                f"{'$' + format(metrics['cac'], '.0f') if metrics['cac'] is not None else 'unknown'}, "
                f"LTV:CAC ratio is {metrics['ltv_cac_ratio'] or 'unknown'}."
            ),
        }
    )

    for stage in compute_funnel(db, company_id):
        documents.append(
            {
                "title": f"Funnel stage: {stage['stage']}",
                "text": (
                    f"At the {stage['stage'].replace('_', ' ')} stage, {stage['users']} users "
                    f"({stage['conversion_rate']:.1%} of signups) have reached this point. "
                    f"Dropoff rate into this stage was {stage['dropoff_rate']:.1%}, an estimated "
                    f"${stage['revenue_impact']:.0f}/mo in lost revenue."
                ),
            }
        )

    leaks = list(db.scalars(select(RevenueLeak).where(RevenueLeak.company_id == company_id)))
    for leak in leaks:
        documents.append(
            {
                "title": f"Revenue leak: {leak.title}",
                "text": f"{leak.description} Category: {leak.category}. Status: {leak.status}.",
            }
        )

    experiments = list(
        db.scalars(select(Experiment).where(Experiment.company_id == company_id))
    )
    for exp in experiments:
        if exp.status == "completed":
            significance = "statistically significant" if exp.result_is_significant else "not statistically significant"
            documents.append(
                {
                    "title": f"Experiment result: {exp.hypothesis[:60]}",
                    "text": (
                        f"Testing '{exp.current_variant}' vs '{exp.suggested_variant}': hypothesis was "
                        f"{exp.hypothesis} Simulated result: control conversion "
                        f"{float(exp.result_control_rate or 0):.1%}, variant conversion "
                        f"{float(exp.result_variant_rate or 0):.1%}, observed uplift "
                        f"{exp.result_observed_uplift_pct}%, p-value {exp.result_p_value} — "
                        f"{significance}."
                    ),
                }
            )
        else:
            documents.append(
                {
                    "title": f"Experiment (unrun): {exp.hypothesis[:60]}",
                    "text": (
                        f"Suggested but not yet simulated: {exp.hypothesis} Proposes changing "
                        f"'{exp.current_variant}' to '{exp.suggested_variant}', expected uplift "
                        f"{exp.expected_uplift_pct}%, expected revenue impact "
                        f"${exp.expected_revenue_impact}/mo."
                    ),
                }
            )

    retention_curve = growth_analytics.compute_retention_curve(db, company_id)
    retention_text = ", ".join(
        f"month {p['month']}: {p['retained_pct']:.0%} retained" if p["retained_pct"] is not None else f"month {p['month']}: not enough data"
        for p in retention_curve
    )
    documents.append({"title": "Customer retention curve", "text": f"Retention by months since conversion — {retention_text}."})

    revenue_metrics = compute_revenue_metrics(db, company_id)
    for row in revenue_metrics["channel_breakdown"]:
        documents.append(
            {
                "title": f"Acquisition channel: {row['channel']}",
                "text": (
                    f"{row['channel']} produced {row['signups']} signups and {row['conversions']} "
                    f"paid conversions ({row['conversion_rate']:.1%} conversion rate), contributing "
                    f"${row['mrr']:.0f}/mo MRR"
                    + (f" at a blended CAC of ${row['cac']:.0f}." if row["cac"] is not None else ".")
                ),
            }
        )

    latest_snapshot = db.scalars(
        select(GrowthTwinSnapshot)
        .where(GrowthTwinSnapshot.company_id == company_id)
        .order_by(GrowthTwinSnapshot.created_at.desc())
        .limit(1)
    ).first()
    if latest_snapshot:
        documents.append(
            {
                "title": "Growth Twin prediction",
                "text": (
                    f"The Growth Twin's latest prediction (conversion model AUC "
                    f"{latest_snapshot.conversion_model_auc}, churn model AUC "
                    f"{latest_snapshot.churn_model_auc}): predicted MRR ${float(latest_snapshot.predicted_mrr):.0f}, "
                    f"predicted churn rate {float(latest_snapshot.predicted_churn_rate):.1%}, predicted paid "
                    f"conversion rate {float(latest_snapshot.predicted_paid_conversion_rate):.1%}."
                ),
            }
        )

    return documents


def retrieve_relevant_context(question: str, documents: list[dict], top_k: int = 5) -> list[dict]:
    if not documents:
        return []

    corpus = [doc["text"] for doc in documents]
    vectorizer = TfidfVectorizer(stop_words="english")
    try:
        tfidf = vectorizer.fit_transform(corpus + [question])
    except ValueError:
        # Empty vocabulary (e.g. question is only stopwords) — fall back to
        # returning the most general documents rather than erroring.
        return documents[:top_k]

    similarities = cosine_similarity(tfidf[-1], tfidf[:-1]).flatten()
    ranked_indices = similarities.argsort()[::-1][:top_k]

    relevant = [documents[i] for i in ranked_indices if similarities[i] > 0]
    return relevant or documents[:top_k]

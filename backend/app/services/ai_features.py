from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.advisor_message import AdvisorMessage
from app.models.revenue_leak import RevenueLeak
from app.models.roadmap_item import RoadmapItem
from app.services import advisor_retrieval, openai_service
from app.services.analytics import compute_dashboard_metrics, compute_funnel

settings = get_settings()


def _has_ai() -> bool:
    return bool(settings.openai_api_key)


def detect_revenue_leaks(db: Session, company_id: int) -> list[RevenueLeak]:
    """Rule-based leak detection over funnel dropoffs, persisted as RevenueLeak rows."""
    stages = compute_funnel(db, company_id)
    leaks: list[RevenueLeak] = []

    for stage in stages:
        if stage["dropoff_rate"] > 0.3 and stage["revenue_impact"] > 0:
            leaks.append(
                RevenueLeak(
                    company_id=company_id,
                    title=f"High dropoff at {stage['stage'].replace('_', ' ')}",
                    stage=stage["stage"],
                    description=(
                        f"{stage['dropoff_rate']:.0%} of users drop off before reaching "
                        f"the {stage['stage'].replace('_', ' ')} stage, costing an estimated "
                        f"${stage['revenue_impact']:.0f}/month in lost revenue."
                    ),
                    category="onboarding_friction" if stage["stage"] != "paid" else "conversion_failure",
                    monthly_impact=stage["revenue_impact"],
                )
            )

    db.query(RevenueLeak).filter(RevenueLeak.company_id == company_id).delete()
    db.add_all(leaks)
    db.commit()
    for leak in leaks:
        db.refresh(leak)
    return leaks


EXPERIMENT_SYSTEM_PROMPT = """You are a senior growth engineer for a B2B SaaS product.
Given funnel and revenue metrics, propose ONE high-leverage A/B test to improve
free trial to paid conversion. Respond with a JSON object with exactly these keys:
hypothesis (string), current_variant (string), suggested_variant (string),
expected_uplift_pct (number), expected_revenue_impact (number, monthly USD),
confidence_score (number between 0 and 1)."""


def _fallback_experiment() -> dict:
    return {
        "hypothesis": (
            "Trial users don't understand the product's value until they see an "
            "AI workflow run, so a more outcome-oriented CTA at signup should raise activation."
        ),
        "current_variant": "Create Workspace",
        "suggested_variant": "Launch Your First AI Workflow",
        "expected_uplift_pct": 12.0,
        "expected_revenue_impact": 4200.0,
        "confidence_score": 0.62,
    }


def generate_experiment(db: Session, company_id: int, focus_area: str | None = None) -> dict:
    if not _has_ai():
        return _fallback_experiment()

    metrics = compute_dashboard_metrics(db, company_id)
    funnel = compute_funnel(db, company_id)
    user_prompt = (
        f"Dashboard metrics: {metrics}\nFunnel stages: {funnel}\n"
        f"Focus area: {focus_area or 'largest funnel dropoff'}"
    )
    try:
        return openai_service.chat_json(EXPERIMENT_SYSTEM_PROMPT, user_prompt)
    except Exception:
        return _fallback_experiment()


ROADMAP_SYSTEM_PROMPT = """You are a product strategist for a B2B SaaS company.
Given funnel and revenue metrics, propose 3-5 roadmap items for the given quarter
that would most increase free trial to paid conversion and expansion revenue.
Respond with a JSON object: {"items": [{"title": string, "description": string,
"revenue_impact": number (monthly USD), "effort": "small"|"medium"|"large",
"confidence_score": number between 0 and 1}, ...]}"""


def _fallback_roadmap_items() -> list[dict]:
    return [
        {
            "title": "Guided first-workflow onboarding",
            "description": "Replace the empty workspace with a guided setup that runs a real AI workflow in under 2 minutes.",
            "revenue_impact": 5200.0,
            "effort": "medium",
            "confidence_score": 0.7,
        },
        {
            "title": "Team invite nudges",
            "description": "Prompt activated users to invite teammates once they've created a project, since invited teams convert at a higher rate.",
            "revenue_impact": 3100.0,
            "effort": "small",
            "confidence_score": 0.6,
        },
        {
            "title": "Usage-based upgrade prompts",
            "description": "Detect trial users approaching plan limits and surface a contextual upgrade prompt instead of a generic paywall.",
            "revenue_impact": 4800.0,
            "effort": "medium",
            "confidence_score": 0.55,
        },
    ]


def generate_roadmap(db: Session, company_id: int, quarter: str) -> list[RoadmapItem]:
    if _has_ai():
        metrics = compute_dashboard_metrics(db, company_id)
        funnel = compute_funnel(db, company_id)
        user_prompt = f"Quarter: {quarter}\nDashboard metrics: {metrics}\nFunnel stages: {funnel}"
        try:
            result = openai_service.chat_json(ROADMAP_SYSTEM_PROMPT, user_prompt)
            items = result["items"]
        except Exception:
            items = _fallback_roadmap_items()
    else:
        items = _fallback_roadmap_items()

    roadmap_items = [
        RoadmapItem(
            company_id=company_id,
            quarter=quarter,
            title=item["title"],
            description=item["description"],
            revenue_impact=item["revenue_impact"],
            effort=item["effort"],
            confidence_score=item["confidence_score"],
        )
        for item in items
    ]
    db.add_all(roadmap_items)
    db.commit()
    for item in roadmap_items:
        db.refresh(item)
    return roadmap_items


ADVISOR_SYSTEM_PROMPT = """You are the AI Founder Advisor inside AI Growth Twin. Answer the
founder's question directly and concisely, grounding every claim in the retrieved context
below rather than inventing numbers, and recommend one concrete next action.

Retrieved context:
{context}"""


def _fallback_advisor_answer(retrieved: list[dict]) -> str:
    if not retrieved:
        return (
            "I can't reach the AI model right now (no OPENAI_API_KEY configured), and there "
            "isn't enough data yet to ground an answer — seed demo data first."
        )
    top = retrieved[0]
    extra = f" Also relevant: {retrieved[1]['title']} — {retrieved[1]['text']}" if len(retrieved) > 1 else ""
    return (
        f"AI reasoning is unavailable right now (no OPENAI_API_KEY configured), so here's the most "
        f"relevant retrieved data instead of a synthesized answer.\n\n{top['title']}: {top['text']}{extra}"
    )


def ask_advisor(db: Session, company_id: int, question: str) -> dict:
    history = list(
        db.scalars(
            select(AdvisorMessage)
            .where(AdvisorMessage.company_id == company_id)
            .order_by(AdvisorMessage.created_at)
        )
    )

    db.add(AdvisorMessage(company_id=company_id, role="user", content=question))
    db.commit()

    knowledge_base = advisor_retrieval.build_knowledge_base(db, company_id)
    retrieved = advisor_retrieval.retrieve_relevant_context(question, knowledge_base, top_k=5)

    if not _has_ai():
        answer = _fallback_advisor_answer(retrieved)
    else:
        context = "\n".join(f"- {doc['title']}: {doc['text']}" for doc in retrieved)
        system_prompt = ADVISOR_SYSTEM_PROMPT.format(context=context)
        messages = [{"role": m.role, "content": m.content} for m in history]
        messages.append({"role": "user", "content": question})
        try:
            answer = openai_service.chat_text(system_prompt, messages)
        except Exception:
            answer = _fallback_advisor_answer(retrieved)

    db.add(AdvisorMessage(company_id=company_id, role="assistant", content=answer))
    db.commit()
    return {"answer": answer, "sources": [doc["title"] for doc in retrieved]}

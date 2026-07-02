"""Real sklearn models backing the Growth Twin: a conversion-probability
classifier and a churn-probability classifier trained on the company's own
trial-user history, replacing the old fixed +2%/-2% heuristic.

With only a few hundred synthetic rows this is intentionally simple (a small
RandomForest and a LogisticRegression) rather than deep learning — the point
is that the numbers are *learned from data* and come with real metrics
(AUC, accuracy, feature importance), not that the model architecture is
sophisticated.
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split

from app.models.trial_user import TrialUser

MIN_ROWS_TO_TRAIN = 20


def _hours_between(start, end) -> float:
    if start is None or end is None:
        return 0.0
    return (end - start).total_seconds() / 3600


def _conversion_features(user: TrialUser) -> dict:
    return {
        "activated": int(user.activated_at is not None),
        "project_created": int(user.project_created_at is not None),
        "team_invited": int(user.team_invited_at is not None),
        "trial_usage": int(user.last_active_at is not None),
        "hours_to_activate": _hours_between(user.signup_at, user.activated_at),
        f"channel={user.channel}": 1,
    }


def _churn_features(user: TrialUser) -> dict:
    return {
        "mrr": float(user.mrr),
        "days_to_convert": _hours_between(user.signup_at, user.converted_at) / 24,
        f"plan={user.plan}": 1,
        f"channel={user.channel}": 1,
    }


def _train_classifier(
    users: list[TrialUser],
    feature_fn,
    label_fn,
    model_factory,
) -> dict:
    feature_dicts = [feature_fn(u) for u in users]
    labels = [label_fn(u) for u in users]

    if len(users) < MIN_ROWS_TO_TRAIN or len(set(labels)) < 2:
        return {
            "model": None,
            "vectorizer": None,
            "auc": None,
            "accuracy": None,
            "feature_importance": {},
            "insufficient_data": True,
            "train_size": 0,
            "test_size": 0,
        }

    vectorizer = DictVectorizer(sparse=False)
    X = vectorizer.fit_transform(feature_dicts)
    y = np.array(labels)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    model = model_factory()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    auc = None
    if len(set(y_test)) > 1:
        y_proba = model.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, y_proba)

    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    else:
        importances = np.abs(model.coef_[0])
        total = importances.sum()
        importances = importances / total if total else importances

    feature_importance = dict(zip(vectorizer.get_feature_names_out(), importances))
    top_importance = dict(
        sorted(feature_importance.items(), key=lambda kv: kv[1], reverse=True)[:8]
    )

    return {
        "model": model,
        "vectorizer": vectorizer,
        "auc": round(float(auc), 4) if auc is not None else None,
        "accuracy": round(float(accuracy), 4),
        "feature_importance": {k: round(float(v), 4) for k, v in top_importance.items()},
        "insufficient_data": False,
        "train_size": len(y_train),
        "test_size": len(y_test),
    }


def train_conversion_model(users: list[TrialUser]) -> dict:
    return _train_classifier(
        users,
        _conversion_features,
        lambda u: int(u.converted_at is not None),
        lambda: RandomForestClassifier(n_estimators=200, max_depth=5, random_state=42),
    )


def train_churn_model(converted_users: list[TrialUser]) -> dict:
    return _train_classifier(
        converted_users,
        _churn_features,
        lambda u: int(u.churned_at is not None),
        lambda: LogisticRegression(max_iter=1000),
    )


def predict_conversion_probabilities(conversion_model: dict, users: list[TrialUser]) -> np.ndarray:
    if conversion_model["model"] is None or not users:
        return np.zeros(len(users))
    X = conversion_model["vectorizer"].transform([_conversion_features(u) for u in users])
    return conversion_model["model"].predict_proba(X)[:, 1]


def predict_churn_probabilities(churn_model: dict, users: list[TrialUser]) -> np.ndarray:
    if churn_model["model"] is None or not users:
        return np.zeros(len(users))
    X = churn_model["vectorizer"].transform([_churn_features(u) for u in users])
    return churn_model["model"].predict_proba(X)[:, 1]

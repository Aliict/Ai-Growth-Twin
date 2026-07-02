from app.services import ml_engine
from tests.conftest import make_trial_user


def _make_conversion_dataset(n_per_class=20):
    users = []
    for i in range(n_per_class):
        users.append(
            make_trial_user(
                company_id=1,
                email=f"converted{i}@example.com",
                activated=True,
                project_created=True,
                team_invited=True,
                trial_usage=True,
                converted=True,
                plan="pro",
                mrr=79.0,
                channel="organic",
            )
        )
    for i in range(n_per_class):
        users.append(
            make_trial_user(company_id=1, email=f"dropped{i}@example.com", channel="paid_search")
        )
    return users


def test_conversion_model_separates_clean_synthetic_data():
    users = _make_conversion_dataset(20)
    result = ml_engine.train_conversion_model(users)

    assert result["insufficient_data"] is False
    assert result["accuracy"] >= 0.9
    assert result["auc"] is not None and result["auc"] >= 0.9
    assert len(result["feature_importance"]) > 0


def test_conversion_model_flags_insufficient_data_below_threshold():
    users = _make_conversion_dataset(5)  # 10 rows, below MIN_ROWS_TO_TRAIN
    result = ml_engine.train_conversion_model(users)

    assert result["insufficient_data"] is True
    assert result["model"] is None
    assert result["feature_importance"] == {}


def test_predict_conversion_probabilities_returns_values_in_range():
    users = _make_conversion_dataset(20)
    model = ml_engine.train_conversion_model(users)
    probs = ml_engine.predict_conversion_probabilities(model, users)

    assert len(probs) == len(users)
    assert all(0.0 <= p <= 1.0 for p in probs)


def test_predict_returns_zeros_when_model_could_not_train():
    users = _make_conversion_dataset(5)
    model = ml_engine.train_conversion_model(users)
    probs = ml_engine.predict_conversion_probabilities(model, users)

    assert all(p == 0.0 for p in probs)


def test_churn_model_trains_on_converted_users_only():
    converted_users = []
    for i in range(15):
        converted_users.append(
            make_trial_user(
                company_id=1,
                email=f"stay{i}@example.com",
                activated=True,
                project_created=True,
                team_invited=True,
                trial_usage=True,
                converted=True,
                plan="business",
                mrr=199.0,
            )
        )
    for i in range(15):
        converted_users.append(
            make_trial_user(
                company_id=1,
                email=f"churn{i}@example.com",
                activated=True,
                project_created=True,
                team_invited=True,
                trial_usage=True,
                converted=True,
                churned=True,
                plan="starter",
                mrr=29.0,
            )
        )

    result = ml_engine.train_churn_model(converted_users)
    assert result["insufficient_data"] is False
    assert result["accuracy"] is not None and result["accuracy"] >= 0.7

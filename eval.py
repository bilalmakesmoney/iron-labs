import json
import re


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def score(expected: str, predicted: str) -> float:
    """
    FABv2 rubric-based scoring.
    expected is a JSON array of {operator, criteria} objects.
    Returns fraction of criteria whose key facts appear in predicted.
    Numeric criteria: check if the number/percentage appears in predicted.
    Qualitative criteria: check >=50% of significant words appear.
    """
    try:
        rubric = json.loads(expected)
        criteria_list = [
            item["criteria"]
            for item in rubric
            if isinstance(item, dict) and "criteria" in item
        ]
    except Exception:
        exp = _normalize(expected)
        pred = _normalize(predicted)
        return 1.0 if exp == pred else (0.5 if exp in pred else 0.0)

    if not criteria_list:
        return 1.0

    pred_lower = _normalize(predicted)
    matched = 0
    for criterion in criteria_list:
        crit_lower = _normalize(criterion)
        # Extract numeric tokens (handles "$1,234.56", "32.82%", "10x", etc.)
        numbers = re.findall(r"[\d,]+\.?\d*\s*(?:%|x\b|million|billion|thousand)?", crit_lower)
        numbers = [n.strip().replace(",", "") for n in numbers if n.strip()]
        if numbers:
            if any(n in pred_lower.replace(",", "") for n in numbers):
                matched += 1
        else:
            # Qualitative: significant-word overlap
            words = [w for w in crit_lower.split() if len(w) > 5]
            if not words:
                matched += 0.5
            elif sum(1 for w in words if w in pred_lower) / len(words) >= 0.5:
                matched += 1

    return matched / len(criteria_list)

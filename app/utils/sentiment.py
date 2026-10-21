from functools import lru_cache

from nltk.sentiment import SentimentIntensityAnalyzer


@lru_cache(maxsize=1)
def _get_sentiment_analyzer() -> SentimentIntensityAnalyzer:
    try:
        return SentimentIntensityAnalyzer()
    except LookupError:
        raise RuntimeError(
            "VADER lexicon is not installed; install it during deployment build"
        ) from None


def get_sentiment_score(text: str) -> float:
    if not text or not text.strip():
        return 0.0
    score = _get_sentiment_analyzer().polarity_scores(text)
    return round(float(score["compound"]), 2)

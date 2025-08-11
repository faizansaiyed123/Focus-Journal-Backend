# utils/sentiment.py
from nltk.sentiment.vader import SentimentIntensityAnalyzer

sentiment_analyzer = SentimentIntensityAnalyzer()


def get_sentiment_score(text: str) -> float:
    score = sentiment_analyzer.polarity_scores(text)
    return round(score["compound"], 2)  # Range: -1 (negative) to +1 (positive)

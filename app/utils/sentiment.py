# # utils/sentiment.py
# from nltk.sentiment.vader import SentimentIntensityAnalyzer

# sentiment_analyzer = SentimentIntensityAnalyzer()


# def get_sentiment_score(text: str) -> float:
#     score = sentiment_analyzer.polarity_scores(text)
#     return round(score["compound"], 2)  # Range: -1 (negative) to +1 (positive)
# utils/sentiment.py
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import ssl
import os

# Handle SSL certificate issues for NLTK downloads
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Initialize sentiment analyzer with automatic data download
sentiment_analyzer = None

def _initialize_sentiment_analyzer():
    """Initialize the sentiment analyzer, downloading data if needed."""
    global sentiment_analyzer
    
    if sentiment_analyzer is None:
        try:
            sentiment_analyzer = SentimentIntensityAnalyzer()
        except LookupError:
            # Download vader_lexicon if not present
            print("Downloading NLTK vader_lexicon data...")
            nltk.download('vader_lexicon', quiet=True)
            sentiment_analyzer = SentimentIntensityAnalyzer()
    
    return sentiment_analyzer

def get_sentiment_score(text: str) -> float:
    """
    Get sentiment score for the given text.
    
    Args:
        text (str): Text to analyze
        
    Returns:
        float: Sentiment score ranging from -1 (negative) to +1 (positive)
    """
    analyzer = _initialize_sentiment_analyzer()
    score = analyzer.polarity_scores(text)
    return round(score["compound"], 2)  # Range: -1 (negative) to +1 (positive)
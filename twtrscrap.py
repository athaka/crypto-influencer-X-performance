#!/usr/bin/python3
# Install required libraries
# !pip install tweepy pandas requests

import tweepy
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
import re

# Twitter API authentication
bearer_token = "AAAAAAAAAAAAAAAAAAAAAIAkzgEAAAAAlnXfREmHOk5lkv6ETn4F2EvWt8Y%3DjkViFnO233zSvr8RguXGLd9xmAhsxh5RQLRtlHqUguFPjmI76G"  # Replace with your token
client = tweepy.Client(bearer_token=bearer_token)

# Fetch CoinGecko coin list for mapping
response = requests.get("https://api.coingecko.com/api/v3/coins/list")
coins = response.json()
symbol_to_id = {coin["symbol"].lower(): coin["id"] for coin in coins}
crypto_terms = set(symbol_to_id.keys())  # Set of symbols to search for

# Function to find cryptocurrency mentions in tweet text
def find_crypto_mentions(tweet_text):
    tweet_lower = tweet_text.lower()
    mentions = []
    for term in crypto_terms:
        if re.search(r'\b' + re.escape(term) + r'\b', tweet_lower):
            mentions.append(term)
    return mentions

# Function to find the closest price to a target timestamp
def find_closest_price(prices, target_timestamp):
    if not prices:
        return None
    closest = min(prices, key=lambda x: abs(x[0] - target_timestamp))
    return closest[1]

# Get influencer and fetch tweets
influencer = input("Enter the Twitter username of the influencer (e.g., VitalikButerin): ").strip()
user = client.get_user(username=influencer)
user_id = user.data.id

current_time = datetime.utcnow().replace(tzinfo=timezone.utc)
since_time = current_time - timedelta(days=1)  # Last 24 hours
tweets = client.get_users_tweets(id=user_id, max_results=100, tweet_fields=["created_at"])
recent_tweets = [tweet for tweet in tweets.data if tweet.created_at >= since_time]
processable_tweets = [tweet for tweet in recent_tweets if tweet.created_at + timedelta(minutes=15) < current_time]

print(f"Found {len(processable_tweets)} tweets from @{influencer} in the last 24 hours with complete price data.")

# Process tweets and fetch price data
data = []
for tweet in processable_tweets:
    tweet_time = tweet.created_at
    tweet_text = tweet.text
    mentions = find_crypto_mentions(tweet_text)
    for mention in mentions:
        coin_id = symbol_to_id.get(mention.lower())
        if coin_id:
            # Fetch 5-minute interval price data for the last day
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=1"
            response = requests.get(url)
            if response.status_code == 200:
                price_data = response.json()["prices"]  # List of [timestamp_ms, price]
                tweet_timestamp = int(tweet_time.timestamp() * 1000)
                price_at_tweet = find_closest_price(price_data, tweet_timestamp)
                price_at_5m = find_closest_price(price_data, tweet_timestamp + 5 * 60 * 1000)
                price_at_10m = find_closest_price(price_data, tweet_timestamp + 10 * 60 * 1000)
                price_at_15m = find_closest_price(price_data, tweet_timestamp + 15 * 60 * 1000)
                percent_change = ((price_at_15m - price_at_tweet) / price_at_tweet) * 100 if price_at_tweet and price_at_15m else None
                data.append({
                    "Influencer": f"@{influencer}",
                    "Token": f"${mention.upper()}",
                    "Tweet Time": tweet_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "Price @Tweet": price_at_tweet,
                    "Price @5m": price_at_5m,
                    "Price @10m": price_at_10m,
                    "Price @15m": price_at_15m,
                    "% Change": percent_change
                })
            else:
                print(f"Failed to fetch price data for {coin_id}")

# Save to CSV
if data:
    df = pd.DataFrame(data)
    filename = f"{influencer}_crypto_performance.csv"
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")
else:
    print("No data to save.")

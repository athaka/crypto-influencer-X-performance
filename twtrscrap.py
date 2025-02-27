#!/usr/bin/python3
# Install required libraries
# !pip install tweepy pandas requests

import tweepy
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
import re
import time

# Twitter API authentication
bearer_token = "your_actual_bearer_token_here"  # Replace with your token
client = tweepy.Client(bearer_token=bearer_token)
print("Twitter API authenticated successfully!")

# Fetch the list of cryptocurrencies from CoinGecko
response = requests.get("https://api.coingecko.com/api/v3/coins/list")
coins = response.json()

# Create a dictionary with symbols and full names
crypto_data = {}
for coin in coins:
    symbol = coin["symbol"].lower()
    name = coin["name"].lower()
    if symbol not in crypto_data:  # Avoid duplicates by using the first occurrence
        crypto_data[symbol] = {"id": coin["id"], "name": name}

# Compile regex patterns for each cryptocurrency
crypto_patterns = {}
for symbol, info in crypto_data.items():
    # Patterns to match $symbol, symbol, and full name
    patterns = [
        rf'\${re.escape(symbol)}\b',  # e.g., $btc
        rf'\b{re.escape(symbol)}\b',  # e.g., btc
        rf'\b{re.escape(info["name"])}\b'  # e.g., bitcoin
    ]
    crypto_patterns[symbol] = re.compile('|'.join(patterns), re.IGNORECASE)

print("CoinGecko coin list with patterns compiled!")

# Prompt user for influencer's Twitter username
influencer = input("Enter the Twitter username of the influencer (e.g., VitalikButerin): ").strip()

# Prompt user for timeframe with clear 7-day limit notice
print("Note: Due to Twitter API free tier restrictions, the maximum timeframe is 7 days.")
days = int(input("Enter the number of days to scan (1 to 7): "))
if days > 7:
    print("Timeframe exceeds the 7-day limit. Setting to 7 days.")
    days = 7
elif days < 1:
    print("Timeframe must be at least 1 day. Setting to 1 day.")
    days = 1

# Fetch the user's Twitter ID
try:
    user = client.get_user(username=influencer)
    user_id = user.data.id
    print(f"Found user ID for @{influencer}")
except Exception as e:
    print(f"Error fetching user: {e}")
    user_id = None

# Fetch tweets if user ID is valid
if user_id:
    # Define the time range (UTC)
    current_time = datetime.utcnow().replace(tzinfo=timezone.utc)
    since_time = current_time - timedelta(days=days)

    # Fetch tweets with pagination (up to ~500 tweets due to free tier limit)
    all_tweets = []
    pagination_token = None
    max_requests = 5  # Approx. 500 tweets (100 per request)
    for i in range(max_requests):
        try:
            tweets = client.get_users_tweets(
                id=user_id,
                max_results=100,  # Max per request in free tier
                tweet_fields=["created_at"],
                start_time=since_time,
                pagination_token=pagination_token
            )
            if tweets.data:
                all_tweets.extend(tweets.data)
            pagination_token = tweets.meta.get("next_token")
            if not pagination_token:
                break  # No more tweets to fetch
            time.sleep(1)  # Delay to respect rate limits
        except tweepy.TooManyRequests:
            print("Twitter API rate limit reached! Waiting 15 minutes...")
            time.sleep(900)  # 15-minute wait
        except Exception as e:
            print(f"Error fetching tweets: {e}")
            break

    # Filter tweets to ensure price data is available
    if days <= 1:
        processable_tweets = [tweet for tweet in all_tweets if tweet.created_at + timedelta(minutes=15) < current_time]
    else:
        processable_tweets = [tweet for tweet in all_tweets if tweet.created_at + timedelta(hours=3) < current_time]
    print(f"Found {len(processable_tweets)} processable tweets from @{influencer} in the last {days} days.")
else:
    print("Cannot proceed without a valid user ID.")
    processable_tweets = []

# Function to detect cryptocurrency mentions in tweet text
def find_crypto_mentions(tweet_text):
    tweet_lower = tweet_text.lower()
    mentions = set()  # Use a set to avoid duplicate mentions
    for symbol, pattern in crypto_patterns.items():
        if pattern.search(tweet_lower):
            mentions.add(symbol)
    return list(mentions)

# Function to find the closest price to a timestamp
def find_closest_price(prices, target_timestamp):
    if not prices:
        return None
    closest = min(prices, key=lambda x: abs(x[0] - target_timestamp))
    return closest[1]

# Process tweets and fetch price data
data = []
for tweet in processable_tweets:
    tweet_time = tweet.created_at
    tweet_text = tweet.text
    mentions = find_crypto_mentions(tweet_text)
    for mention in mentions:
        coin_id = crypto_data[mention]["id"]
        # Adjust CoinGecko API days parameter
        cg_days = min(days, 90) if days > 1 else 1
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={cg_days}"
        response = requests.get(url)
        if response.status_code == 200:
            price_data = response.json()["prices"]
            tweet_timestamp = int(tweet_time.timestamp() * 1000)  # CoinGecko uses milliseconds
            price_at_tweet = find_closest_price(price_data, tweet_timestamp)

            if days <= 1:
                # 5-minute intervals for ≤1 day
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
                # Hourly intervals for >1 day
                price_at_1h = find_closest_price(price_data, tweet_timestamp + 1 * 60 * 60 * 1000)
                price_at_2h = find_closest_price(price_data, tweet_timestamp + 2 * 60 * 60 * 1000)
                price_at_3h = find_closest_price(price_data, tweet_timestamp + 3 * 60 * 60 * 1000)
                percent_change = ((price_at_3h - price_at_tweet) / price_at_tweet) * 100 if price_at_tweet and price_at_3h else None
                data.append({
                    "Influencer": f"@{influencer}",
                    "Token": f"${mention.upper()}",
                    "Tweet Time": tweet_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "Price @Tweet": price_at_tweet,
                    "Price @1h": price_at_1h,
                    "Price @2h": price_at_2h,
                    "Price @3h": price_at_3h,
                    "% Change": percent_change
                })
        else:
            print(f"Failed to fetch price data for {coin_id} (status code: {response.status_code})")
        time.sleep(1)  # Respect CoinGecko rate limits (10-50 calls/min)

# Display and save the results
if data:
    df = pd.DataFrame(data)
    print(df)
    filename = f"{influencer}_crypto_performance_{days}days.csv"
    df.to_csv(filename, index=False)
    print(f"Results saved to {filename}")
else:
    print("No data to display or save. Either no tweets were found or no crypto mentions were detected.")

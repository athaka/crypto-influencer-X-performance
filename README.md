# Practice Task: Analyst Module (Phase 1 - Data Extraction & Processing)
---
## Objective
This is a module to track Twitter influencers, extract Contract Addresses (CA) from their posts, and analyze price movements. It will help identify potential trading patterns by tracking price action at 5-minute, 10-minute, and 15-minute intervals after an influencer's tweet. Focus is the Solana blockchain.

**Simple use case:** Anyone should be able to give this system an influencer's X profile and a timeline, say 90 days. It goes in, scans the influencer's posts through the last 90 days, and returns a list that tracks the performance of this influencer's calls.

## Key Deliverables (Phase 1 - MVP)

### Monitor Selected Twitter Accounts
- Detect when an influencer tweets about a token.
- Extract Contract Address (CA), Token Ticker, and Timestamp from their tweet.
- If the tweet only contains a ticker (e.g., $SOL), fetch the CA.

### Fetch Price Data
- Retrieve historical price data of the token after the influencer's tweet.
- Store price movement for 5 min, 10 min, 15 min intervals.
- Structure data to log price changes over time.

### Store & Structure Data
- Output structured data in a readable format (Google Sheets, CSV, or Database).
- Ensure the system can handle multiple influencers and tokens efficiently.
- AI Query System – Allow interactive search for querying insights.

### Example Output
Influencer	|Token	CA	        |Tweet Time	|Price @5m	|Price @10m	|Price @15m	|% Change
@elonmusk	|$DOGE	0x123...abc	|10:00 AM	|$0.08	    |$0.085	    |$0.09	    |+12%


## Technical Requirements
- **Languages:** Python (preferred), Node.js (optional).
- **APIs:** (Left blank on purpose)
- **Storage:** Google Sheets, CSV, or SQL/NoSQL database.
- **Performance:** Ensure speed & scalability for multiple influencers.

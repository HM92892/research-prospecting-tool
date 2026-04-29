# Research & Prospecting Tool

A web app that takes a company URL and outputs:
- An offer recommendation (SQL or MQL) with reasoning
- 3 cold email campaigns with full follow-up sequences (Creative Ideas, Signal-Based, Case Study)
- A one-page company brief with a reply talk-track

Built around Eric Nowoslawski's outbound framework: offer beats list, list beats personalization, personalization beats volume.

## Why I built this

I'm interviewing for SDR roles. The hardest part of cold outreach is figuring out what to actually offer a specific company. Most tools optimize the wrong layer, sending more emails or swapping a name token. The real lift is offer quality. I built this to learn that craft.

## How it works

1. You paste a company URL
2. The scraper hits the homepage and 20 subpages (about, customers, case studies, careers, etc.) in parallel
3. Claude extracts the company's intelligence: named customers, value props, recent signals, GTM motion
4. A second Claude call generates 3 campaign types with full follow-up sequences
5. A third Claude call produces a one-page brief with a reply talk-track

Whole pipeline runs in about 15-30 seconds. Each company costs approximately $0.04 in Claude API calls.

## Stack

- Python 3.11
- Flask
- Anthropic Claude Sonnet 4
- BeautifulSoup + requests for scraping

## Run locally

1. `pip install -r requirements.txt`
2. Set `ANTHROPIC_API_KEY` in your environment
3. `python app.py`
4. Open `http://localhost:5000`

## What I'd add next

- Cold call opener, 30-second pitch, and objection responses per campaign
- Spam-phrase checker on generated emails
- A/B variant generation per campaign
- Tests

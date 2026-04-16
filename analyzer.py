"""
AI analysis engine for the Research & Prospecting Tool.
Uses Claude to extract company intelligence and generate prospecting outputs.
"""

import anthropic
import os
import json
import re

MODEL = "claude-sonnet-4-20250514"


def _get_client():
    """Get Anthropic client."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set. Add it to your environment variables.")
    return anthropic.Anthropic(api_key=api_key)


def _call_claude(system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> str:
    """Call Claude API and return response text."""
    client = _get_client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text


# ============================================================
# STEP 1: Company Analysis
# ============================================================

ANALYSIS_SYSTEM = """You are a B2B sales intelligence analyst. You extract actionable information from company websites for outbound prospecting teams.

Rules:
- Be specific and factual. Only report what is explicitly stated on the website.
- Never guess or infer things that aren't there.
- Use exact names, numbers, and quotes from the website.
- If something isn't found, say "Not found on website" rather than guessing."""

ANALYSIS_PROMPT = """Analyze this company's website content and extract the following. Be specific and use exact names, numbers, and quotes from the website.

WEBSITE CONTENT:
{all_text}

Extract the following in this exact format:

## COMPANY NAME
The company's name.

## ONE-LINER
What this company does in one sentence. Be specific, not "they help businesses grow" but exactly what their product/service is and who it serves.

## WHO THEY SERVE
Their target customer. Include specific industries, company sizes, or job roles if mentioned.

## NAMED CUSTOMERS
List every specific company name mentioned as a customer, client, or case study. Include the result they achieved if mentioned. If no customers are named, write "Not found on website."

## CASE STUDIES
For each case study found, provide the customer name, their problem, and the result with exact numbers. If none found, write "Not found on website."

## KEY VALUE PROPOSITIONS
The top 3 specific problems this company solves. Not vague benefits. Specific problems with specific solutions. For example, not "saves time" but "eliminates manual LinkedIn research for SDR teams by automating prospect enrichment."

## PROOF POINTS
Any specific metrics, numbers, or claims. Examples: "50+ data sources", "10,000+ customers", "2x pipeline." List them all.

## PRICING MODEL
How they charge (per seat, usage-based, freemium, enterprise only, etc.) if visible on the website. If not visible, write "Not found on website."

## RECENT NEWS OR BLOG HIGHLIGHTS
Any recent announcements, product launches, blog post topics, or company news found on the site. If none, write "Not found on website."

## GTM MOTION
Analyze whether this company uses Product-Led Growth (PLG), Sales-Led, or a Hybrid approach. Look for signals like: free trial/freemium CTAs (PLG), "Get a demo" / "Contact sales" CTAs (Sales-Led), community size, enterprise compliance badges (SOC 2, GDPR), dedicated enterprise pages, self-serve signup flows. Explain your reasoning with specific evidence from the website.
"""


def analyze_company(scraped_data: dict) -> str:
    """Analyze scraped website data and return structured company intelligence."""
    return _call_claude(
        ANALYSIS_SYSTEM,
        ANALYSIS_PROMPT.format(all_text=scraped_data["all_text"]),
    )


# ============================================================
# STEP 2: Multi-Campaign Email Generation
# ============================================================

EMAIL_SYSTEM = """You are a cold email strategist who follows Eric Nowoslawski's (Growth Engine X) outbound methodology. You have studied his complete framework across 216 videos.

Your core beliefs based on Eric's verified framework:

OFFER PHILOSOPHY:
- Offer quality is the #1 variable in outbound. Offer > List > Personalization > Volume.
- The best offer solves the prospect's problem for free BEFORE the demo.
- Use "the sawdust principle": give away what costs little to you but is valuable to the prospect.
- Frame offers as "a repeatable framework/system" not just "a service."
- Test what's easy to say yes to first. For most markets, lead magnets (MQL) should be tested before direct asks (SQL).

PERSONALIZATION HIERARCHY (never violate this):
- Level 1: Strong signal available -> Use Recency Waterfall (LinkedIn post, new in role, company news, blog, product launch)
- Level 2: No strong signal but research capacity -> Use Creative Ideas campaign (3 specific ideas for their business)
- Level 3: No signal, no research capacity -> Use Lead Magnet approach (free value, no personalization needed)
- Level 4: Generic AI personalization ("I saw you work in fintech") -> NEVER. Gets 143% fewer replies.

EMAIL RULES:
- 70-90 words. Under 70 lacks credibility, over 90 drops response.
- Subject lines: 2-3 words max. Must pass "would a colleague send this?" test.
- First line: Reference something specific (Recency Waterfall) or lead with value. Never "I saw you're in marketing."
- CTA: Interest-based, not meeting-based. "Would this be useful?" not "Book a demo." Be specific about what you're offering.
- No em dashes anywhere. No exclamation points. No "I hope this finds you well." No corporate jargon.
- Write at a fifth-grade reading level. Clear, direct, human.
- PS line: Offer a different value prop than the main body. Name-drop other people at the company if possible.
- Reference real case studies generically (outcome over company name). "We helped an enterprise company scale from 5 to 20 reps" beats "We helped Coca-Cola."

CAMPAIGN TYPES:
1. Creative Ideas Campaign (Eric's highest performer): 3 bullet points showing specific ways you could help them. Each idea must be concrete and specific to their business.
2. Signal-Based Campaign: Use Recency Waterfall triggers. Reference something recent and verifiable about the prospect or company.
3. Case Study Campaign: Reference their own customers' success stories. "I saw you helped [customer] achieve [result]. How are you finding more customers like them?"
"""

EMAIL_PROMPT = """Based on this company analysis, generate cold email campaigns that THIS company could use for outbound prospecting to THEIR prospects.

COMPANY ANALYSIS:
{company_analysis}

Generate 3 distinct campaign types. For each one, provide the output in this exact JSON structure:

```json
{{
  "campaigns": [
    {{
      "type": "Creative Ideas Campaign",
      "badge_color": "blue",
      "description": "Three specific ideas showing how you could help the prospect. Eric's highest-performing campaign type.",
      "offer_name": "Short catchy name, 3-5 words",
      "what_youre_giving": "2-3 sentences. What does the prospect get for free?",
      "why_it_converts": "1-2 sentences on why a cold prospect says yes.",
      "target_icp": "Specific job titles, company size, industry, and any signals to look for",
      "apollo_search": "Exact job titles to search + filters (industry, headcount, location)",
      "linkedin_search": "LinkedIn Sales Navigator search query with filters",
      "subject_line": "2-3 words max",
      "email_body": "The full email. 70-90 words. Must include 3 numbered ideas specific to the prospect's business. Interest-based CTA.",
      "ps_line": "Different value prop than main body. Optional name-drop."
    }},
    {{
      "type": "Signal-Based Campaign",
      "badge_color": "green",
      "description": "Uses Recency Waterfall triggers. References something recent and verifiable.",
      "offer_name": "...",
      "what_youre_giving": "...",
      "why_it_converts": "...",
      "target_icp": "...",
      "apollo_search": "...",
      "linkedin_search": "...",
      "subject_line": "...",
      "email_body": "...",
      "ps_line": "..."
    }},
    {{
      "type": "Case Study Campaign",
      "badge_color": "orange",
      "description": "References the company's own customer success stories to build credibility.",
      "offer_name": "...",
      "what_youre_giving": "...",
      "why_it_converts": "...",
      "target_icp": "...",
      "apollo_search": "...",
      "linkedin_search": "...",
      "subject_line": "...",
      "email_body": "...",
      "ps_line": "..."
    }}
  ]
}}
```

CRITICAL RULES:
- Every email must reference REAL information from the company analysis. If no case studies were found, use specific proof points or value props instead.
- Subject lines: 2-3 words, looks like it came from a coworker.
- Email body: 70-90 words. No em dashes. No exclamation points. No filler. Fifth-grade reading level.
- CTA: Easier than "book a demo." Examples: "Want me to send it over?", "Worth a look?", "Would any of these be useful?"
- Apollo searches: Include 3-5 specific job titles, not just "decision makers."
- The Creative Ideas email MUST have 3 numbered, specific ideas. Not generic.
- The Signal-Based email must specify which Recency Waterfall trigger to use and include a template variable like [recent LinkedIn post topic] where the signal goes.
- The Case Study email must reference a real customer or outcome from the analysis.

Return ONLY the JSON. No other text before or after it."""


def generate_campaigns(company_analysis: str) -> list[dict]:
    """Generate multi-campaign emails based on company analysis. Returns list of campaign dicts."""
    raw = _call_claude(
        EMAIL_SYSTEM,
        EMAIL_PROMPT.format(company_analysis=company_analysis),
        max_tokens=4096,
    )

    # Extract JSON from response
    try:
        # Try to find JSON block
        json_match = re.search(r"```json\s*(.*?)\s*```", raw, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
        else:
            # Try parsing the whole thing
            data = json.loads(raw)
        return data.get("campaigns", [])
    except (json.JSONDecodeError, AttributeError):
        # If JSON parsing fails, return raw text wrapped in a structure
        return [{"type": "Raw Output", "email_body": raw, "error": "Could not parse structured output"}]


# ============================================================
# STEP 3: Company Brief
# ============================================================

BRIEF_SYSTEM = """You are a B2B sales research analyst creating a one-page company brief for an SDR. The brief should contain everything an SDR needs to have an informed first conversation with someone at this company. Be concise and actionable."""

BRIEF_PROMPT = """Create a one-page company brief based on this analysis. Format it for quick scanning by an SDR before a call or outreach.

COMPANY ANALYSIS:
{company_analysis}

Output format (use markdown):

# [Company Name] - Prospecting Brief

## What They Do
[2-3 sentences. Plain English. What problem do they solve and for whom.]

## Their Customers
[Bullet list of named customers with any results mentioned. If none found, note that.]

## Why Prospects Buy From Them
[Top 3 reasons based on their value props and proof points. Each one sentence.]

## Potential Pain Points to Probe
[3-4 questions an SDR could ask that tie to problems this company solves. Frame as discovery questions.]

## Competitive Landscape
[Who else operates in this space? What makes this company different based on their website claims?]

## Talk Track for Replies
[If a prospect responds "tell me more" to your cold email, here's a 4-5 sentence response that:
- Acknowledges their interest without being salesy
- Drops one specific proof point
- Offers a concrete next step (not just "let's chat")
Keep it under 80 words. No em dashes.]

## Key Numbers
[Any metrics, stats, or proof points from their site. Bullet list.]
"""


def generate_brief(company_analysis: str) -> str:
    """Generate a one-page company brief for SDR use."""
    return _call_claude(
        BRIEF_SYSTEM,
        BRIEF_PROMPT.format(company_analysis=company_analysis),
    )


# ============================================================
# Full Pipeline
# ============================================================

def run_full_pipeline(scraped_data: dict) -> dict:
    """Run the complete analysis pipeline. Returns all outputs."""
    # Step 1: Analyze company
    analysis = analyze_company(scraped_data)

    # Step 2: Generate campaigns
    campaigns = generate_campaigns(analysis)

    # Step 3: Generate brief
    brief = generate_brief(analysis)

    return {
        "company_analysis": analysis,
        "campaigns": campaigns,
        "brief": brief,
        "url": scraped_data["url"],
        "domain": scraped_data["company_domain"],
        "pages_scraped": scraped_data["pages_found"],
        "chars_scraped": scraped_data["total_chars"],
        "from_cache": scraped_data.get("from_cache", False),
    }

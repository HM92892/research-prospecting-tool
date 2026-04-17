"""
AI analysis engine for the Research & Prospecting Tool v2.
Uses Claude to extract company intelligence and generate prospecting outputs.
Now supports seller context for personalized outreach.
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


def _parse_json_response(raw: str) -> dict:
    """Extract JSON from Claude response, handling markdown code blocks."""
    try:
        json_match = re.search(r"```json\s*(.*?)\s*```", raw, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        json_match = re.search(r"\{[\s\S]*\}", raw)
        if json_match:
            return json.loads(json_match.group(0))
        return json.loads(raw)
    except (json.JSONDecodeError, AttributeError):
        return {}


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
Any recent announcements, product launches, blog post topics, or company news found on the site. Pick the 2-3 MOST RECENT items and note what they are about. If none, write "Not found on website."

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
# STEP 2: Offer Recommendation + Multi-Campaign Emails
# ============================================================

def _build_seller_context(seller_info: dict) -> str:
    """Build seller context string from optional inputs."""
    if not seller_info or not seller_info.get("company_name"):
        return ""

    parts = []
    parts.append(f"SELLER COMPANY: {seller_info['company_name']}")
    if seller_info.get("what_you_sell"):
        parts.append(f"WHAT THEY SELL: {seller_info['what_you_sell']}")
    if seller_info.get("customer_wins"):
        parts.append(f"PROOF/CUSTOMER WINS:\n{seller_info['customer_wins']}")
    if seller_info.get("buyer_persona"):
        parts.append(f"TYPICAL BUYER PERSONA: {seller_info['buyer_persona']}")

    return "\n\n".join(parts)


EMAIL_SYSTEM = """You are a cold email strategist who follows Eric Nowoslawski's (Growth Engine X) outbound methodology. You have studied his complete framework across 216 videos.

OFFER PHILOSOPHY:
- Offer quality is the #1 variable. Offer > List > Personalization > Volume.
- The best offer solves the prospect's problem for free BEFORE the demo.
- "The sawdust principle": give away what costs little to you but is valuable to the prospect.
- Test what's easy to say yes to first. For most markets, lead magnets (MQL) beat direct asks (SQL).

OFFER DECISION TREE (Eric's core framework):
- SQL (direct meeting ask): Use when problem is urgent, pain is obvious, and saying yes is easy. Example: "You're not collecting sales tax in 3 states."
- MQL (lead magnet / free value): Use when problem isn't acute, multiple stakeholders involved, or market is crowded. Example: "Free audit of your current enrichment coverage."
- Rule: "Every time we've made a major shift from SQL to MQL, we've seen the biggest jumps in success."

PERSONALIZATION HIERARCHY (never violate):
- Level 1: Strong signal -> Recency Waterfall (LinkedIn post, new role, company news, blog, product launch)
- Level 2: No signal but research capacity -> Creative Ideas campaign (3 specific ideas)
- Level 3: No signal, no capacity -> Lead Magnet approach (free value, no personalization)
- Level 4: Generic AI personalization ("I saw you work in fintech") -> NEVER. 143% fewer replies.

EMAIL RULES:
- 70-90 words. Under 70 lacks credibility, over 90 drops response.
- Subject lines: 2-3 words max. "Would a colleague send this?" test.
- CTA: Interest-based, not meeting-based. "Would this be useful?" not "Book a demo."
- No em dashes. No exclamation points. No "I hope this finds you well." No corporate jargon.
- Fifth-grade reading level. Clear, direct, human.
- PS line: Different value prop than main body.
- Reference case studies generically (outcome > company name).

FOLLOW-UP RULES (Eric's sequence data):
- Email 2: Flip the value prop. If email 1 pitches "save time," email 2 pitches "make money." Lower the ask from SQL to MQL.
- Email 3: Free value taste. Do actual work for them (small piece). Law of reciprocity.
- Timing: 3-5 days between emails. Then 1-3 months before contacting again.

IMPLICIT OBJECTION FRAMEWORK:
- For every email, identify what a cold reader's instinctive objection would be.
- Address it directly with a poke-the-bear question or mechanism proof.
- Example: "We save you money on taxes" raises "I already have an accountant." Fix: "How do you know your current accountant is using every legal loophole?"
"""

EMAIL_PROMPT_WITH_SELLER = """You are writing cold emails FROM {seller_name} TO prospects at the target company below.

SELLER CONTEXT:
{seller_context}

TARGET COMPANY ANALYSIS:
{company_analysis}

MOST RECENT SIGNAL FROM TARGET (for signal-based email):
Look for the most recent news, blog post, or announcement in the analysis above. Use that as the signal. If none found, use "new in role" as the default trigger.

---

First, provide an OFFER RECOMMENDATION in this format:

OFFER_RECOMMENDATION: [SQL or MQL]
OFFER_REASONING: [1-2 sentences explaining why, based on Eric's decision tree. Consider: Is the pain obvious? Is the ask easy to say yes to? Is the market crowded?]

---

Then generate 3 campaign types. Each campaign must include the primary email (Email 1) plus two follow-ups (Email 2 and Email 3).

Return the output in this exact JSON structure:

```json
{{
  "offer_recommendation": "SQL or MQL",
  "offer_reasoning": "1-2 sentence explanation",
  "campaigns": [
    {{
      "type": "Creative Ideas Campaign",
      "badge_color": "blue",
      "description": "Three specific ideas showing how {seller_name} could help the prospect.",
      "offer_name": "Short catchy name, 3-5 words",
      "what_youre_giving": "2-3 sentences. What does the prospect get for free?",
      "why_it_converts": "1-2 sentences on why a cold prospect says yes.",
      "implicit_objection": "What a cold reader immediately thinks when reading this email, and how the email handles it.",
      "target_icp": "Specific job titles, company size, industry, signals",
      "apollo_search": "Exact job titles + filters (industry, headcount, location)",
      "linkedin_search": "LinkedIn Sales Navigator search query with filters",
      "subject_line": "2-3 words max",
      "email_body": "Email 1. 70-90 words. Must include 3 numbered ideas specific to their business. Interest-based CTA.",
      "ps_line": "Different value prop than main body.",
      "followup_2_subject": "2-3 words",
      "followup_2_body": "Email 2. 50-70 words. Flip the value prop. Lower the ask. Different angle than email 1.",
      "followup_3_subject": "2-3 words",
      "followup_3_body": "Email 3. 40-60 words. Free value taste. Offer a small piece of actual work you already did for them."
    }},
    {{
      "type": "Signal-Based Campaign",
      "badge_color": "green",
      "description": "Uses the most recent signal from the target company as the hook.",
      "offer_name": "...",
      "what_youre_giving": "...",
      "why_it_converts": "...",
      "implicit_objection": "...",
      "target_icp": "...",
      "apollo_search": "...",
      "linkedin_search": "...",
      "subject_line": "...",
      "email_body": "Email 1. 70-90 words. References a REAL recent signal from the analysis (blog post, news, product launch). If none found, uses new-in-role trigger.",
      "ps_line": "...",
      "followup_2_subject": "...",
      "followup_2_body": "Email 2. Flip value prop, lower ask.",
      "followup_3_subject": "...",
      "followup_3_body": "Email 3. Free value taste."
    }},
    {{
      "type": "Case Study Campaign",
      "badge_color": "orange",
      "description": "Uses proof from {seller_name}'s customer wins to build credibility.",
      "offer_name": "...",
      "what_youre_giving": "...",
      "why_it_converts": "...",
      "implicit_objection": "...",
      "target_icp": "...",
      "apollo_search": "...",
      "linkedin_search": "...",
      "subject_line": "...",
      "email_body": "Email 1. 70-90 words. References a real customer win from the seller context. Uses generic outcome framing (not company name).",
      "ps_line": "...",
      "followup_2_subject": "...",
      "followup_2_body": "Email 2. Different case study or proof point. Lower ask.",
      "followup_3_subject": "...",
      "followup_3_body": "Email 3. Free value taste."
    }}
  ]
}}
```

CRITICAL RULES:
- All emails are FROM {seller_name} TO prospects at the target company.
- Email 1: 70-90 words. Email 2: 50-70 words. Email 3: 40-60 words.
- No em dashes anywhere. No exclamation points. No filler.
- Subject lines: 2-3 words, colleague test.
- Each follow-up MUST have a different angle/value prop than the previous email.
- Email 2 should lower the ask (if email 1 was SQL, email 2 should be MQL).
- Email 3 should give free value (a list, an audit snippet, a finding).
- The implicit_objection field should name the objection AND explain how the email handles it.
- If seller context is provided, use their actual proof/customer wins. If not, generate based on the target company analysis.

Return ONLY the JSON. No other text."""

EMAIL_PROMPT_NO_SELLER = """You are analyzing a target company and generating cold email campaigns that could be used to prospect this company.

TARGET COMPANY ANALYSIS:
{company_analysis}

MOST RECENT SIGNAL FROM TARGET (for signal-based email):
Look for the most recent news, blog post, or announcement in the analysis above. Use that as the signal. If none found, use "new in role" as the default trigger.

---

First, provide an OFFER RECOMMENDATION:

Imagine you are a company selling to this target. Based on Eric's SQL vs MQL decision tree, should the approach be SQL (direct ask) or MQL (lead magnet)? Consider their GTM motion, company size, and market.

---

Then generate 3 campaign types with Email 1 + two follow-ups each.

Return the output in this exact JSON structure:

```json
{{
  "offer_recommendation": "SQL or MQL",
  "offer_reasoning": "1-2 sentence explanation",
  "campaigns": [
    {{
      "type": "Creative Ideas Campaign",
      "badge_color": "blue",
      "description": "Three specific ideas showing how you could help the prospect.",
      "offer_name": "Short catchy name, 3-5 words",
      "what_youre_giving": "2-3 sentences.",
      "why_it_converts": "1-2 sentences.",
      "implicit_objection": "What a cold reader thinks, and how the email handles it.",
      "target_icp": "Specific job titles, company size, industry, signals",
      "apollo_search": "Exact job titles + filters",
      "linkedin_search": "LinkedIn Sales Navigator query",
      "subject_line": "2-3 words max",
      "email_body": "Email 1. 70-90 words.",
      "ps_line": "Different value prop.",
      "followup_2_subject": "2-3 words",
      "followup_2_body": "Email 2. 50-70 words. Flip value prop, lower ask.",
      "followup_3_subject": "2-3 words",
      "followup_3_body": "Email 3. 40-60 words. Free value taste."
    }},
    {{
      "type": "Signal-Based Campaign",
      "badge_color": "green",
      "description": "Uses the most recent signal from the target company.",
      "offer_name": "...", "what_youre_giving": "...", "why_it_converts": "...",
      "implicit_objection": "...", "target_icp": "...", "apollo_search": "...",
      "linkedin_search": "...", "subject_line": "...",
      "email_body": "Email 1. 70-90 words. References real recent signal from analysis.",
      "ps_line": "...",
      "followup_2_subject": "...", "followup_2_body": "Email 2. 50-70 words.",
      "followup_3_subject": "...", "followup_3_body": "Email 3. 40-60 words."
    }},
    {{
      "type": "Case Study Campaign",
      "badge_color": "orange",
      "description": "References the target company's own customer success stories.",
      "offer_name": "...", "what_youre_giving": "...", "why_it_converts": "...",
      "implicit_objection": "...", "target_icp": "...", "apollo_search": "...",
      "linkedin_search": "...", "subject_line": "...",
      "email_body": "Email 1. 70-90 words. References their customers' success.",
      "ps_line": "...",
      "followup_2_subject": "...", "followup_2_body": "Email 2. 50-70 words.",
      "followup_3_subject": "...", "followup_3_body": "Email 3. 40-60 words."
    }}
  ]
}}
```

CRITICAL RULES:
- Email 1: 70-90 words. Email 2: 50-70 words. Email 3: 40-60 words.
- No em dashes. No exclamation points. No filler. Fifth-grade reading level.
- Subject lines: 2-3 words, colleague test.
- Each follow-up has a different angle. Email 2 lowers the ask. Email 3 gives free value.
- The implicit_objection field names the objection AND how the email handles it.

Return ONLY the JSON."""


def generate_campaigns(company_analysis: str, seller_info: dict = None) -> dict:
    """Generate campaigns with offer recommendation. Returns dict with recommendation + campaigns."""
    seller_context = _build_seller_context(seller_info) if seller_info else ""

    if seller_context:
        prompt = EMAIL_PROMPT_WITH_SELLER.format(
            seller_name=seller_info.get("company_name", "Your Company"),
            seller_context=seller_context,
            company_analysis=company_analysis,
        )
    else:
        prompt = EMAIL_PROMPT_NO_SELLER.format(company_analysis=company_analysis)

    raw = _call_claude(EMAIL_SYSTEM, prompt, max_tokens=6000)
    data = _parse_json_response(raw)

    if not data:
        return {
            "offer_recommendation": "Could not determine",
            "offer_reasoning": "",
            "campaigns": [{"type": "Raw Output", "email_body": raw, "error": "Could not parse structured output"}],
        }

    return {
        "offer_recommendation": data.get("offer_recommendation", ""),
        "offer_reasoning": data.get("offer_reasoning", ""),
        "campaigns": data.get("campaigns", []),
    }


# ============================================================
# STEP 3: Company Brief
# ============================================================

BRIEF_SYSTEM = """You are a B2B sales research analyst creating a one-page company brief for an SDR. The brief should contain everything an SDR needs to have an informed first conversation with someone at this company. Be concise and actionable."""

BRIEF_PROMPT = """Create a one-page company brief based on this analysis. Format it for quick scanning by an SDR before a call or outreach.

COMPANY ANALYSIS:
{company_analysis}

{seller_section}

Output format (use markdown):

# [Company Name] - Prospecting Brief

## What They Do
[2-3 sentences. Plain English.]

## Their Customers
[Bullet list of named customers with results. If none found, note that.]

## Why Prospects Buy From Them
[Top 3 reasons. Each one sentence.]

## Potential Pain Points to Probe
[3-4 discovery questions an SDR could ask that tie to problems this company solves.]

## Competitive Landscape
[Who else operates in this space? What makes this company different?]

## Talk Track for Replies
[If a prospect responds "tell me more," here's a 4-5 sentence response. Under 80 words. No em dashes. Acknowledges interest, drops a proof point, offers concrete next step.]

## Key Numbers
[Metrics, stats, proof points from their site. Bullet list.]
"""


def generate_brief(company_analysis: str, seller_info: dict = None) -> str:
    """Generate a one-page company brief."""
    seller_section = ""
    if seller_info and seller_info.get("company_name"):
        seller_section = f"""SELLER CONTEXT (tailor the brief for someone selling from this company):
Company: {seller_info.get('company_name', '')}
What they sell: {seller_info.get('what_you_sell', '')}
Customer wins: {seller_info.get('customer_wins', '')}
Buyer persona: {seller_info.get('buyer_persona', '')}

Tailor the "Pain Points to Probe" and "Talk Track" to be relevant for someone selling {seller_info.get('company_name', 'this product')} to the target company."""

    return _call_claude(
        BRIEF_SYSTEM,
        BRIEF_PROMPT.format(company_analysis=company_analysis, seller_section=seller_section),
    )


# ============================================================
# Full Pipeline
# ============================================================

def run_full_pipeline(scraped_data: dict, seller_info: dict = None) -> dict:
    """Run the complete analysis pipeline. Returns all outputs."""
    # Step 1: Analyze target company
    analysis = analyze_company(scraped_data)

    # Step 2: Generate campaigns with offer recommendation
    campaign_data = generate_campaigns(analysis, seller_info)

    # Step 3: Generate brief
    brief = generate_brief(analysis, seller_info)

    return {
        "company_analysis": analysis,
        "offer_recommendation": campaign_data.get("offer_recommendation", ""),
        "offer_reasoning": campaign_data.get("offer_reasoning", ""),
        "campaigns": campaign_data.get("campaigns", []),
        "brief": brief,
        "url": scraped_data["url"],
        "domain": scraped_data["company_domain"],
        "pages_scraped": scraped_data["pages_found"],
        "chars_scraped": scraped_data["total_chars"],
        "from_cache": scraped_data.get("from_cache", False),
        "has_seller_context": bool(seller_info and seller_info.get("company_name")),
    }

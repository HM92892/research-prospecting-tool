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

## RECENT NEWS OR BLOG HIGHLIGHTS
Any recent announcements, product launches, blog post topics, or company news found on the site. Pick the 2-3 MOST RECENT items and note what they are about. If none, write "Not found on website."

## GTM MOTION
Start your answer with EXACTLY one of these labels on the first line — do not add any other words on that line:
Sales-Led
Product-Led (PLG)
Hybrid

Then on the following lines, explain your reasoning with specific evidence from the website. Look for signals like: free trial/freemium CTAs (PLG), "Get a demo" / "Contact sales" CTAs (Sales-Led), community size, enterprise compliance badges (SOC 2, GDPR), dedicated enterprise pages, self-serve signup flows.

## LIKELY BUYERS
Based on the website content, case studies, testimonials, and "who we serve" sections, identify:
- The job titles most likely to purchase this type of product (e.g., VP Sales, Head of Marketing, CTO)
- The departments involved in the buying decision
- The seniority level of the typical buyer
- Any specific buyer personas mentioned on the site (e.g., "sales leaders at B2B SaaS companies")
"""


def analyze_company(scraped_data: dict) -> str:
    """Analyze scraped website data and return structured company intelligence."""
    return _call_claude(
        ANALYSIS_SYSTEM,
        ANALYSIS_PROMPT.format(all_text=scraped_data["all_text"]),
    )


# ============================================================
# STEP 2: ICP Profile Generation
# ============================================================

ICP_SYSTEM = """You are an ICP (Ideal Customer Profile) specialist helping B2B sales teams define hyper-specific buyer profiles for outbound prospecting. You output precise, immediately actionable targeting criteria."""

ICP_PROMPT = """Based on the company analysis below, generate a structured ICP profile that a sales rep can use immediately for prospecting.

COMPANY ANALYSIS:
{company_analysis}

{seller_section}

{linkedin_section}

Generate a structured ICP profile in this exact JSON format:

```json
{{
  "target_titles": ["3-5 specific job titles ordered by priority. Be exact: 'VP of Sales Development' not 'sales leader'. Base these on who would champion or purchase the seller's product at this type of company."],
  "target_industries": ["2-4 specific industries. Examples: 'B2B SaaS', 'Sales Technology', 'Revenue Operations'"],
  "company_size": "Specific headcount range based on the target company's customer base. Example: '50-500 employees'",
  "key_signals": ["3-4 specific buying signals. Examples: 'Actively hiring SDR managers (job postings)', 'Announced Series B or later funding', 'Using Salesforce or HubSpot (tech stack signal)', 'VP of Sales hired in last 6 months'"],
  "apollo_search": "Ready-to-paste Apollo search. Format exactly as: Title: [comma-separated titles] | Industry: [industries] | Employees: [range] | Keywords: [relevant keywords]",
  "linkedin_search": "Ready-to-paste LinkedIn Sales Navigator search. Format exactly as: Title: [titles] | Industry: [industries] | Company headcount: [range] | Geography: United States | Seniority: [Director, VP, C-Level]",
  "icp_reasoning": "2-3 sentences explaining why this ICP was chosen based on the company's actual customers, case studies, and GTM motion.",
  "linkedin_profiles_analyzed": 0
}}
```

Rules:
- Be hyper-specific. Every field should be immediately usable without editing.
- Base job titles on who would actually buy or champion the seller's specific product.
- Base industries on who the target company actually serves (their customers).
- Search queries must be copy-pasteable with no placeholders.
- If LinkedIn profile URLs were provided, set linkedin_profiles_analyzed to the count and refine titles/industries based on URL slug patterns (names, companies visible in URLs).

Return ONLY the JSON. No other text."""


def _extract_linkedin_urls(buyer_persona: str) -> list:
    """Extract LinkedIn URLs from the buyer persona field."""
    if not buyer_persona:
        return []
    import re
    urls = re.findall(r'https?://(?:www\.)?linkedin\.com/in/[^\s,;]+', buyer_persona)
    return urls


def generate_icp_profile(company_analysis: str, seller_info: dict = None) -> dict:
    """Generate a structured ICP profile. Returns dict with targeting fields."""
    seller_section = ""
    linkedin_section = ""

    if seller_info:
        parts = []
        if seller_info.get("what_you_sell"):
            parts.append(f"PRODUCT BEING SOLD: {seller_info['what_you_sell']}")
        if seller_info.get("customer_wins"):
            parts.append(f"SELLER'S PROOF POINTS:\n{seller_info['customer_wins']}")
        if parts:
            seller_section = "SELLER CONTEXT:\n" + "\n\n".join(parts)

        linkedin_urls = _extract_linkedin_urls(seller_info.get("buyer_persona", ""))
        if linkedin_urls:
            url_list = "\n".join(f"- {u}" for u in linkedin_urls)
            linkedin_section = f"""SAMPLE BUYER LINKEDIN PROFILES (Option B — URL inference):
The SDR provided these LinkedIn profile URLs as examples of their ideal buyer. Based on the URL patterns (which often contain the person's name and company slug), infer what you can about the buyer persona — titles, seniority level, company type. Use this to refine the ICP definition and search queries. Set linkedin_profiles_analyzed to {len(linkedin_urls)}.

{url_list}"""

    prompt = ICP_PROMPT.format(
        company_analysis=company_analysis,
        seller_section=seller_section,
        linkedin_section=linkedin_section,
    )

    raw = _call_claude(ICP_SYSTEM, prompt, max_tokens=2000)
    data = _parse_json_response(raw)

    if not data:
        return {
            "target_titles": [],
            "target_industries": [],
            "company_size": "",
            "key_signals": [],
            "apollo_search": "",
            "linkedin_search": "",
            "icp_reasoning": "",
            "linkedin_profiles_analyzed": 0,
        }

    return data


# ============================================================
# STEP 3: Offer Recommendation + Multi-Campaign Emails
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

Then generate 3 campaign types. EVERY campaign MUST include Email 1 PLUS Email 2 AND Email 3 follow-ups. No exceptions. All 3 campaigns must have all 3 emails.

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
      "implicit_objection": "Name the specific implicit objection (what the cold reader ACTUALLY thinks, not the surface reaction), then explain exactly which part of the email addresses it and how. 2-3 sentences minimum.",
      "target_icp": "Specific job titles, company size, industry, signals",
      "apollo_search": "Exact job titles + filters (industry, headcount, location)",
      "linkedin_search": "LinkedIn Sales Navigator search query with filters",
      "subject_line": "2-3 words max",
      "email_body": "Email 1. 70-90 words. Must include 3 numbered ideas that are SPECIFIC to the target company's situation, product, or recent activity. NOT generic value props of {seller_name}. Each idea should connect {seller_name}'s capability to something unique about THIS company. Interest-based CTA.",
      "ps_line": "Different value prop than main body.",
      "followup_2_subject": "2-3 words, different from email 1 subject",
      "followup_2_body": "Email 2. 60-80 words. REQUIRED. Flip the value prop completely. If email 1 was about efficiency, email 2 is about revenue. If email 1 was about data coverage, email 2 is about time savings. Lower the ask. Different angle.",
      "followup_3_subject": "2-3 words, different from emails 1 and 2",
      "followup_3_body": "Email 3. 50-70 words. REQUIRED. Free value taste. Reference a specific piece of work you already did or could do for them. Law of reciprocity. Example: 'Ran a quick analysis on companies in your space and found 3 data sources most teams miss.'"
    }},
    {{
      "type": "Signal-Based Campaign",
      "badge_color": "green",
      "description": "Uses the most recent signal from the target company as the hook.",
      "offer_name": "Short catchy name, 3-5 words",
      "what_youre_giving": "2-3 sentences. What does the prospect get for free?",
      "why_it_converts": "1-2 sentences on why a cold prospect says yes.",
      "implicit_objection": "Name the specific implicit objection (what the cold reader ACTUALLY thinks, not the surface reaction), then explain exactly which part of the email addresses it and how. 2-3 sentences minimum.",
      "target_icp": "Specific job titles, company size, industry, signals",
      "apollo_search": "Exact job titles + filters (industry, headcount, location)",
      "linkedin_search": "LinkedIn Sales Navigator search query with filters",
      "subject_line": "2-3 words max",
      "email_body": "Email 1. 70-90 words. References a REAL recent signal from the analysis (blog post, news, product launch, hiring). If none found, uses new-in-role trigger.",
      "ps_line": "Different value prop than main body.",
      "followup_2_subject": "2-3 words, different from email 1 subject",
      "followup_2_body": "Email 2. 60-80 words. REQUIRED. Flip the value prop. Different angle from email 1. Lower the ask.",
      "followup_3_subject": "2-3 words, different from emails 1 and 2",
      "followup_3_body": "Email 3. 50-70 words. REQUIRED. Free value taste. Offer something tangible."
    }},
    {{
      "type": "Case Study Campaign",
      "badge_color": "orange",
      "description": "Uses proof from {seller_name}'s customer wins to build credibility.",
      "offer_name": "Short catchy name, 3-5 words",
      "what_youre_giving": "2-3 sentences. What does the prospect get for free?",
      "why_it_converts": "1-2 sentences on why a cold prospect says yes.",
      "implicit_objection": "Name the specific implicit objection (what the cold reader ACTUALLY thinks, not the surface reaction), then explain exactly which part of the email addresses it and how. 2-3 sentences minimum.",
      "target_icp": "Specific job titles, company size, industry, signals",
      "apollo_search": "Exact job titles + filters (industry, headcount, location)",
      "linkedin_search": "LinkedIn Sales Navigator search query with filters",
      "subject_line": "2-3 words max",
      "email_body": "Email 1. 70-90 words. References a real customer win from the seller context. Uses generic outcome framing (not company name unless it's a well-known logo).",
      "ps_line": "Different value prop than main body.",
      "followup_2_subject": "2-3 words, different from email 1 subject",
      "followup_2_body": "Email 2. 60-80 words. REQUIRED. Different case study or proof point than email 1. Lower ask. Flip angle.",
      "followup_3_subject": "2-3 words, different from emails 1 and 2",
      "followup_3_body": "Email 3. 50-70 words. REQUIRED. Free value taste. Offer a quick audit, analysis, or finding."
    }}
  ]
}}
```

CRITICAL RULES:
- All emails are FROM {seller_name} TO prospects at the target company.
- EVERY campaign must have all fields filled in. Do NOT use "..." as a value. Do NOT skip followup_2 or followup_3 for ANY campaign.
- Email 1: 70-90 words. Email 2: 60-80 words. Email 3: 50-70 words.
- No em dashes anywhere. No exclamation points. No filler.
- Emails should sound conversational, like a real person typing. Use contractions (don't, we're, that's). Start sentences with "So" or "Just" when natural. Never say "I hope this finds you well" or "I wanted to reach out."
- Subject lines: 2-3 words, lowercase, colleague test.
- Creative Ideas MUST be specific to the target company's product, customers, or recent activity. NOT generic {seller_name} value props. Each idea should make the reader think "they actually understand our business."
- Each follow-up MUST have a different angle/value prop than the previous email.
- Email 2 should lower the ask (if email 1 was SQL, email 2 should be MQL).
- Email 3 should give free value (a list, an audit snippet, a finding).
- The implicit_objection field must go DEEP. Not "they already have tools." What is the REAL fear or concern? Example: "The real objection isn't that they have tools, it's that adding another vendor to an already complex stack means more integration work, more vendor management, and the risk of looking foolish if it doesn't deliver. The email handles this by..."
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

Then generate 3 campaign types. EVERY campaign MUST include Email 1 PLUS Email 2 AND Email 3 follow-ups. No exceptions. All 3 campaigns must have all 3 emails.

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
      "implicit_objection": "Name the specific implicit objection (what the cold reader ACTUALLY thinks, not the surface reaction), then explain exactly which part of the email addresses it and how. 2-3 sentences minimum.",
      "target_icp": "Specific job titles, company size, industry, signals",
      "apollo_search": "Exact job titles + filters",
      "linkedin_search": "LinkedIn Sales Navigator query",
      "subject_line": "2-3 words max",
      "email_body": "Email 1. 70-90 words. 3 ideas that are specific to THIS company's situation, not generic.",
      "ps_line": "Different value prop.",
      "followup_2_subject": "2-3 words, different from email 1 subject",
      "followup_2_body": "Email 2. 60-80 words. REQUIRED. Flip value prop, lower ask, different angle.",
      "followup_3_subject": "2-3 words, different from emails 1 and 2",
      "followup_3_body": "Email 3. 50-70 words. REQUIRED. Free value taste. Offer something tangible."
    }},
    {{
      "type": "Signal-Based Campaign",
      "badge_color": "green",
      "description": "Uses the most recent signal from the target company.",
      "offer_name": "Short catchy name, 3-5 words",
      "what_youre_giving": "2-3 sentences.",
      "why_it_converts": "1-2 sentences.",
      "implicit_objection": "Name the specific implicit objection (what the cold reader ACTUALLY thinks, not the surface reaction), then explain exactly which part of the email addresses it and how. 2-3 sentences minimum.",
      "target_icp": "Specific job titles, company size, industry, signals",
      "apollo_search": "Exact job titles + filters",
      "linkedin_search": "LinkedIn Sales Navigator query",
      "subject_line": "2-3 words max",
      "email_body": "Email 1. 70-90 words. References real recent signal from analysis.",
      "ps_line": "Different value prop.",
      "followup_2_subject": "2-3 words, different from email 1 subject",
      "followup_2_body": "Email 2. 60-80 words. REQUIRED. Flip value prop, lower ask.",
      "followup_3_subject": "2-3 words, different from emails 1 and 2",
      "followup_3_body": "Email 3. 50-70 words. REQUIRED. Free value taste."
    }},
    {{
      "type": "Case Study Campaign",
      "badge_color": "orange",
      "description": "References the target company's own customer success stories.",
      "offer_name": "Short catchy name, 3-5 words",
      "what_youre_giving": "2-3 sentences.",
      "why_it_converts": "1-2 sentences.",
      "implicit_objection": "Name the specific implicit objection (what the cold reader ACTUALLY thinks, not the surface reaction), then explain exactly which part of the email addresses it and how. 2-3 sentences minimum.",
      "target_icp": "Specific job titles, company size, industry, signals",
      "apollo_search": "Exact job titles + filters",
      "linkedin_search": "LinkedIn Sales Navigator query",
      "subject_line": "2-3 words max",
      "email_body": "Email 1. 70-90 words. References their customers' success.",
      "ps_line": "Different value prop.",
      "followup_2_subject": "2-3 words, different from email 1 subject",
      "followup_2_body": "Email 2. 60-80 words. REQUIRED. Different proof point, lower ask.",
      "followup_3_subject": "2-3 words, different from emails 1 and 2",
      "followup_3_body": "Email 3. 50-70 words. REQUIRED. Free value taste."
    }}
  ]
}}
```

CRITICAL RULES:
- EVERY campaign must have all fields filled in. Do NOT use "..." as a value. Do NOT skip followup_2 or followup_3 for ANY campaign.
- Email 1: 70-90 words. Email 2: 60-80 words. Email 3: 50-70 words.
- No em dashes. No exclamation points. No filler. Fifth-grade reading level.
- Emails should sound conversational. Use contractions. Never say "I hope this finds you well" or "I wanted to reach out."
- Subject lines: 2-3 words, lowercase, colleague test.
- Each follow-up has a different angle. Email 2 lowers the ask. Email 3 gives free value.
- The implicit_objection field must go deep, not surface-level. What is the REAL fear or concern beneath the stated objection?

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
# STEP 4: Company Brief
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
[You are the SELLER responding to someone at the target company who replied "sure, tell me more" to your cold email. NOT a pitch from the target company. Write a 4-5 sentence reply as the seller. Under 80 words. No em dashes. Acknowledge their reply, drop a relevant proof point about YOUR product/service, connect it to THEIR situation, and offer a concrete next step (quick call, audit, resource). Conversational tone, like a real person replying to an email.]

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
    # Step 1: Analyze target company (extract intelligence + likely buyers)
    analysis = analyze_company(scraped_data)

    # Step 2: Generate ICP profile (structured targeting block)
    icp_profile = generate_icp_profile(analysis, seller_info)

    # Step 3: Generate campaigns with offer recommendation
    campaign_data = generate_campaigns(analysis, seller_info)

    # Step 4: Generate company brief / intel
    brief = generate_brief(analysis, seller_info)

    return {
        "company_analysis": analysis,
        "icp_profile": icp_profile,
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

# File: run_daily.py
from __future__ import annotations
import os, json, pytz
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from adapters.headlines_rss import get_headlines
from adapters.markets_yf import get_markets_snapshot
from adapters.econ_calendar_stub import get_today_calendar
from delivery.emailer import send_email
from jinja2 import Template
from textwrap import dedent
from openai import OpenAI

# ⬇️ Prompts now imported from prompts.py
from prompts import SYSTEM_PROMPT, ADVISOR_BRIEF_PROMPT, CLIENT_SAFE_PROMPT

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "gpt-4o-mini")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_APP_PASSWORD = os.getenv("SENDER_APP_PASSWORD")
RECIPIENTS = [e.strip() for e in os.getenv("RECIPIENTS", "").split(",") if e.strip()]
TIMEZONE = os.getenv("TIMEZONE", "America/New_York")
ENFORCE_830 = os.getenv("ENFORCE_830_ET", "false").lower() == "true"

client = OpenAI(api_key=OPENAI_API_KEY)

class Headline(BaseModel):
    title: str
    source: str
    url: str
    published: str

class FactBundle(BaseModel):
    run_id: str = Field(default_factory=lambda: datetime.now().astimezone(pytz.timezone(TIMEZONE)).isoformat())
    indices: dict = {}
    rates_fx: dict = {}
    commodities: dict = {}
    vol_credit: dict = {}
    overnight: dict = {}
    calendar_today: list = []
    headlines: list[Headline] = []
    audit: dict = {}

EMAIL_HTML_TMPL = Template(dedent(
    """
    <div style="font-family:Inter,Arial,sans-serif;font-size:14px;line-height:1.45;color:#111">
      <h3 style="margin:0 0 8px">Daily Macro — {{ ts_local }}</h3>
      <p style="white-space:pre-wrap">{{ advisor }}</p>
      <hr style="border:none;border-top:1px solid #ddd;margin:12px 0"/>
      <h4 style="margin:0 0 6px">Client-Safe</h4>
      <p style="white-space:pre-wrap">{{ client }}</p>
      <p style="font-size:12px;color:#666;margin-top:12px">For informational purposes only. Not a recommendation. Sources: public data.</p>
    </div>
    """
))

def build_fact_bundle() -> FactBundle:
    tz = pytz.timezone(TIMEZONE)
    now_local = datetime.now(tz)

    m = get_markets_snapshot()
    indices = {k: {"pct": m.get(k)} for k in ["ES", "NQ", "DJ"]}
    rates_fx = {"UST10y_pctchg": m.get("UST10Y"), "DXY_pct": m.get("DXY")}
    commodities = {"WTI_pct": m.get("WTI"), "Gold_pct": m.get("GOLD")}
    vol_credit = {"VIX_lvl_pct": m.get("VIX")}

    cal = get_today_calendar(TIMEZONE)
    heads = [Headline(**h) for h in get_headlines(max_items=6)]

    audit = {
        "sources": ["RSS", "YahooFinance"],
        "generated_at": now_local.isoformat(),
    }

    return FactBundle(
        indices=indices,
        rates_fx=rates_fx,
        commodities=commodities,
        vol_credit=vol_credit,
        calendar_today=cal,
        headlines=heads,
        audit=audit,
    )

def _render_with_llm(bundle: FactBundle) -> tuple[str, str]:
    facts_json = bundle.model_dump()

    adv_resp = client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps({"FACT_BUNDLE": facts_json})},
            {"role": "user", "content": ADVISOR_BRIEF_PROMPT},
        ],
        temperature=0.2,
        max_output_tokens=300,
    )
    advisor_text = adv_resp.output_text

    client_resp = client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps({"FACT_BUNDLE": facts_json, "ADVISOR_BRIEF": advisor_text})},
            {"role": "user", "content": CLIENT_SAFE_PROMPT},
        ],
        temperature=0.2,
        max_output_tokens=300,
    )
    client_text = client_resp.output_text

    return advisor_text, client_text

def main():
    if not (OPENAI_API_KEY and SENDER_EMAIL and SENDER_APP_PASSWORD and RECIPIENTS):
        raise SystemExit("Missing required env vars. See .env.example or GitHub Secrets")

    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    if ENFORCE_830 and (now.hour != 8 or now.minute != 30):
        raise SystemExit("Skipping run: not 8:30 AM ET")

    try:
        bundle = build_fact_bundle()
        advisor_text, client_text = _render_with_llm(bundle)
    except Exception as e:
        advisor_text = (
            "Data unavailable from public sources at this time. We'll retry next run.\n"
            f"Reason: {e}"
        )
        client_text = (
            "Markets update is temporarily unavailable. We’re checking feeds and will resume shortly.\n"
            "Sources: public government & exchange data."
        )

    ts_local = now.strftime("%a %b %d, %Y — %I:%M %p %Z")
    html = EMAIL_HTML_TMPL.render(ts_local=ts_local, advisor=advisor_text, client=client_text)
    subject = f"Daily Macro — {ts_local}"

    send_email(SENDER_EMAIL, SENDER_APP_PASSWORD, RECIPIENTS, subject, html, text=None)

    os.makedirs(".out", exist_ok=True)
    try:
        with open(f".out/bundle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w", encoding="utf-8") as f:
            payload = bundle.model_dump() if 'bundle' in locals() else {"error": "no bundle", "ts": ts_local}
            json.dump(payload, f, indent=2)
    except Exception:
        pass

if __name__ == "__main__":
    main()

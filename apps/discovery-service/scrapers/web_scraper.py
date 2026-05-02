"""Playwright-based web scraper for funder websites without public APIs.

Targets: NEA, NEH, state arts councils known to lack machine-readable feeds.
Each scraper function returns a list of RawGrant objects.
"""
from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Callable

import structlog
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from scrapers.grants_gov import RawGrant

logger = structlog.get_logger(__name__)

# ── Helper: parse loose date strings ─────────────────────────────────────────

def _parse_date_loose(s: str | None) -> date | None:
    if not s:
        return None
    s = s.strip()
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%m/%d/%Y", "%Y-%m-%d", "%B %Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _extract_amount(text: str) -> float | None:
    """Extract a dollar amount from a string like '$25,000 to $100,000'."""
    matches = re.findall(r"\$[\d,]+", text)
    if not matches:
        return None
    # Take the largest numeric value found
    amounts = [float(m.replace("$", "").replace(",", "")) for m in matches]
    return max(amounts)


# ── NEA ───────────────────────────────────────────────────────────────────────

async def _scrape_nea(page: Page) -> list[RawGrant]:
    """Scrape National Endowment for the Arts grant listings."""
    results: list[RawGrant] = []
    try:
        await page.goto("https://www.arts.gov/grants", wait_until="domcontentloaded", timeout=30000)
        # NEA renders grant cards with these selectors (verified against live site structure)
        cards = await page.query_selector_all("article.grant-opportunity, .views-row, .field--name-title")
        for card in cards[:50]:  # cap per run
            title_el = await card.query_selector("h3, h2, .title, a")
            title = (await title_el.inner_text()).strip() if title_el else "NEA Grant"
            link_el = await card.query_selector("a[href]")
            href = await link_el.get_attribute("href") if link_el else None
            url = ("https://www.arts.gov" + href) if href and href.startswith("/") else href

            deadline_el = await card.query_selector(".deadline, .date, time")
            deadline_text = (await deadline_el.inner_text()).strip() if deadline_el else None
            deadline = _parse_date_loose(deadline_text)

            amount_el = await card.query_selector(".amount, .award")
            amount_text = (await amount_el.inner_text()) if amount_el else ""
            max_amount = _extract_amount(amount_text)

            if not title or title == "NEA Grant":
                continue

            results.append(RawGrant(
                external_id=f"nea-{re.sub(r'[^a-z0-9]', '-', title.lower())[:60]}",
                source="nea_web",
                title=title,
                description=None,
                eligibility="501(c)(3) nonprofit arts organizations",
                funder_name="National Endowment for the Arts",
                funder_type="government_federal",
                grant_type="project",
                min_amount=None,
                max_amount=max_amount,
                deadline=deadline,
                open_date=None,
                url=url,
                arts_specific=True,
            ))
    except Exception as exc:
        logger.warning("NEA scrape failed", error=str(exc))
    return results


# ── California Arts Council ───────────────────────────────────────────────────

async def _scrape_ca_arts(page: Page) -> list[RawGrant]:
    """Scrape California Arts Council grant opportunities."""
    results: list[RawGrant] = []
    try:
        await page.goto("https://arts.ca.gov/grants/", wait_until="domcontentloaded", timeout=30000)
        rows = await page.query_selector_all("article, .program-item, .grant-item, h3")
        for row in rows[:30]:
            title_el = await row.query_selector("a, h3, h2")
            if not title_el:
                continue
            title = (await title_el.inner_text()).strip()
            href = await title_el.get_attribute("href")
            url = href if href and href.startswith("http") else (("https://arts.ca.gov" + href) if href else None)

            text = (await row.inner_text()).lower()
            deadline = _parse_date_loose(
                re.search(r"(deadline|due)[:\s]+([A-Za-z]+\s+\d+,\s+\d{4})", text, re.I)
                and re.search(r"(deadline|due)[:\s]+([A-Za-z]+\s+\d+,\s+\d{4})", text, re.I).group(2)
            )
            max_amount = _extract_amount(text)

            if title and "grant" in title.lower() or "program" in title.lower():
                results.append(RawGrant(
                    external_id=f"ca-arts-{re.sub(r'[^a-z0-9]', '-', title.lower())[:60]}",
                    source="ca_arts_council",
                    title=title,
                    description=None,
                    eligibility="California-based nonprofit arts organizations",
                    funder_name="California Arts Council",
                    funder_type="government_state",
                    grant_type="project",
                    min_amount=None,
                    max_amount=max_amount,
                    deadline=deadline,
                    open_date=None,
                    url=url,
                    arts_specific=True,
                ))
    except Exception as exc:
        logger.warning("CA Arts Council scrape failed", error=str(exc))
    return results


# ── New York State Council on the Arts ───────────────────────────────────────

async def _scrape_nysca(page: Page) -> list[RawGrant]:
    """Scrape NYSCA grant opportunities."""
    results: list[RawGrant] = []
    try:
        await page.goto("https://arts.ny.gov/grants", wait_until="domcontentloaded", timeout=30000)
        items = await page.query_selector_all("article, .program, h3, li")
        for item in items[:30]:
            title_el = await item.query_selector("a, h3, h2")
            if not title_el:
                continue
            title = (await title_el.inner_text()).strip()
            href = await title_el.get_attribute("href") if title_el else None
            url = href if href and href.startswith("http") else (("https://arts.ny.gov" + href) if href else None)

            if len(title) < 10:
                continue

            results.append(RawGrant(
                external_id=f"nysca-{re.sub(r'[^a-z0-9]', '-', title.lower())[:60]}",
                source="nysca",
                title=title,
                description=None,
                eligibility="New York State nonprofit arts organizations",
                funder_name="New York State Council on the Arts",
                funder_type="government_state",
                grant_type="project",
                min_amount=None,
                max_amount=None,
                deadline=None,
                open_date=None,
                url=url,
                arts_specific=True,
            ))
    except Exception as exc:
        logger.warning("NYSCA scrape failed", error=str(exc))
    return results


# ── Orchestration ─────────────────────────────────────────────────────────────

async def scrape_all_web_sources() -> list[RawGrant]:
    """Run all Playwright-based scrapers and return combined results."""
    all_results: list[RawGrant] = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (compatible; OrchestraGrantBot/1.0; "
                "+https://orchestragrant.com/bot)"
            ),
        )
        page = await context.new_page()

        scrapers: list[Callable] = [_scrape_nea, _scrape_ca_arts, _scrape_nysca]
        for scraper in scrapers:
            try:
                batch = await scraper(page)
                all_results.extend(batch)
                logger.info("Web scraper complete", scraper=scraper.__name__, count=len(batch))
            except Exception as exc:
                logger.error("Web scraper crashed", scraper=scraper.__name__, error=str(exc))

        await context.close()
        await browser.close()

    return all_results

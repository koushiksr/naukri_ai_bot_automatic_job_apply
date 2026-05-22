"""
naukri_jobs.py
──────────────
Playwright utilities for Naukri job listing pages.

Usage
-----
    from playwright.sync_api import sync_playwright
    from naukri_jobs import JobList

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://www.naukri.com/jobs-in-india")

        jobs = JobList(page)

        job = jobs[0]                      # first listing
        print(job.get_role())              # "NBBL- Associate/Senior Associate - Data Analyst"
        print(job.get_salary())            # "Not disclosed"
        print(job.is_women_only())         # True
        print(job.get_skills())            # ["Data Analysis", "AI", ...]

        # Click only if "Python" is in skills AND "Java" is NOT
        jobs[1].click_if(must_have=["Python"], must_not_have=["Java"])
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import re
from playwright.sync_api import Page, Locator


# ─────────────────────────────────────────────
#  SELECTORS  (single source of truth)
# ─────────────────────────────────────────────
class _Sel:
    # container
    ARTICLE         = "article.jobTuple"

    # header
    ROLE            = "p.title"
    COMPANY         = "span.subTitle"
    RATING          = "span.starRating .typ-12Bold"

    # inline facts  (li icons differ only by class suffix)
    EXPERIENCE      = "li.experience span"
    SALARY          = "li.salary span"
    LOCATION        = "li.location span"

    # body
    JD_TEXT         = "div.job-description span"

    # tags
    SKILL_TAGS      = "ul.tags li"

    # footer badges
    WOMEN_ONLY_PILL = "div.pill-container.type span.label"   # "Prefers women"
    URGENT_BADGE    = "span.urgent-hiring"                   # exists only when urgent
    POSTED_DATE     = "div.type span.fw500"
    HIDE_BTN        = ".naukicon-ot-hide"


# ─────────────────────────────────────────────
#  JOB  (wraps a single <article> locator)
# ─────────────────────────────────────────────
class Job:
    """
    Represents one job card on a Naukri listing page.
    All getters are lazy — they query the DOM on demand.
    """

    def __init__(self, locator: Locator, index: int) -> None:
        self._loc   = locator          # scoped to <article>
        self.index  = index

    # ── identity ──────────────────────────────

    def get_role(self) -> str:
        """Job title / role name."""
        return self._text(_Sel.ROLE)

    def get_company(self) -> str:
        """Company name."""
        return self._text(_Sel.COMPANY)

    def get_rating(self) -> Optional[str]:
        """Ambition Box star rating, or None if absent."""
        return self._maybe_text(_Sel.RATING)

    def get_job_id(self) -> Optional[str]:
        """data-job-id attribute of the article element."""
        return self._loc.get_attribute("data-job-id")

    # ── facts ─────────────────────────────────

    def get_experience(self) -> str:
        """Experience range, e.g. '3-6 Yrs'."""
        return self._text(_Sel.EXPERIENCE)

    def get_salary(self) -> str:
        """Salary string, e.g. '7-15 Lacs PA' or 'Not disclosed'."""
        return self._text(_Sel.SALARY)

    def get_location(self) -> str:
        """Location string, e.g. 'Mumbai (All Areas)(Goregaon), Hyderabad(Narsingi)'."""
        return self._text(_Sel.LOCATION)

    def get_locations(self) -> list[str]:
        """Location split into a list of individual cities/areas."""
        raw = self.get_location()
        return [loc.strip() for loc in raw.split(",") if loc.strip()]

    def get_posted_date(self) -> str:
        """Relative date string, e.g. '1 Day Ago', '17 Days Ago'."""
        return self._text(_Sel.POSTED_DATE)

    # ── description & skills ──────────────────

    def get_jd(self) -> str:
        """Truncated job description snippet shown on the card."""
        return self._text(_Sel.JD_TEXT)

    def get_skills(self) -> list[str]:
        """List of skill tags, e.g. ['Python', 'SQL', 'Power BI']."""
        tags = self._loc.locator(_Sel.SKILL_TAGS).all()
        return [t.inner_text().strip() for t in tags if t.inner_text().strip()]

    def has_skill(self, keyword: str, case_sensitive: bool = False) -> bool:
        """True if *keyword* appears as a distinct word in any of the skills list."""
        skills = self.get_skills()
        if not case_sensitive:
            keyword = keyword.lower()
            skills  = [s.lower() for s in skills]
        return any(re.search(rf'\b{re.escape(keyword)}\b', s) for s in skills)

    # ── flags ─────────────────────────────────

    def is_women_only(self) -> bool:
        """True when the card shows a 'Prefers women' diversity pill."""
        label = self._maybe_text(_Sel.WOMEN_ONLY_PILL)
        return label is not None and "women" in label.lower()

    def is_urgent_hiring(self) -> bool:
        """True when an urgent-hiring badge is visible on the card."""
        badge = self._loc.locator(_Sel.URGENT_BADGE)
        return badge.count() > 0 and badge.first.is_visible()

    def is_remote(self) -> bool:
        """True when location contains 'remote'."""
        return "remote" in self.get_location().lower()

    def is_salary_disclosed(self) -> bool:
        """False when salary is 'Not disclosed'."""
        return "not disclosed" not in self.get_salary().lower()

    # ── rich summary ──────────────────────────

    def summary(self) -> dict:
        """Return all card data as a plain dict (good for logging/export)."""
        return {
            "index":          self.index,
            "job_id":         self.get_job_id(),
            "role":           self.get_role(),
            "company":        self.get_company(),
            "rating":         self.get_rating(),
            "experience":     self.get_experience(),
            "salary":         self.get_salary(),
            "location":       self.get_location(),
            "posted":         self.get_posted_date(),
            "jd":             self.get_jd(),
            "skills":         self.get_skills(),
            "women_only":     self.is_women_only(),
            "urgent_hiring":  self.is_urgent_hiring(),
            "remote":         self.is_remote(),
        }

    # ── interactions ──────────────────────────

    def click(self) -> None:
        """Click the job card (opens detail page / side panel)."""
        self._loc.locator(_Sel.ROLE).click()

    def hide(self) -> None:
        """Click the hide button so the job does not appear in future searches."""
        try:
            self._loc.locator(_Sel.HIDE_BTN).first.click(timeout=2000)
        except:
            pass

    def click_if(
        self,
        must_have:     Optional[list[str]] = None,
        must_not_have: Optional[list[str]] = None,
        case_sensitive: bool = False,
    ) -> bool:
        """
        Click the job only when keyword conditions are satisfied.

        Parameters
        ----------
        must_have      : keywords that MUST appear in the job card text
        must_not_have  : keywords that must NOT appear in the job card text
        case_sensitive : default False

        Returns True if the job was clicked, False if skipped.

        Example
        -------
        job.click_if(must_have=["Python", "SQL"], must_not_have=["Java"])
        """
        card_text = self._full_text()
        if not case_sensitive:
            card_text = card_text.lower()

        if must_have:
            found = False
            for kw in must_have:
                needle = kw if case_sensitive else kw.lower()
                if needle in card_text:
                    found = True
                    break
            if not found:
                return False

        for kw in (must_not_have or []):
            needle = kw if case_sensitive else kw.lower()
            if needle in card_text:
                return False

        self.click()
        return True

    # ── private helpers ───────────────────────

    def _text(self, selector: str) -> str:
        el = self._loc.locator(selector).first
        return el.inner_text().strip() if el.count() else ""

    def _maybe_text(self, selector: str) -> Optional[str]:
        el = self._loc.locator(selector)
        if el.count() == 0:
            return None
        return el.first.inner_text().strip() or None

    def _full_text(self) -> str:
        """All visible text on the card (for keyword matching)."""
        return self._loc.inner_text()

    def __repr__(self) -> str:
        return f"<Job[{self.index}] role={self.get_role()!r}>"


# ─────────────────────────────────────────────
#  JOB LIST  (wraps the full listing page)
# ─────────────────────────────────────────────
class JobList:
    """
    Manages all job cards on the current Playwright page.

    Supports:
        jobs[0]                   – get Job by index
        len(jobs)                 – total cards
        for job in jobs           – iterate
        jobs.get(2)               – same as jobs[2] but explicit
        jobs.filter(...)          – return subset as new list
        jobs.click_first_matching – click the first card that passes keywords
    """

    def __init__(self, page: Page, article_selector: str = _Sel.ARTICLE) -> None:
        self._page = page
        self._sel  = article_selector

    # ── core access ───────────────────────────

    def _articles(self) -> list[Locator]:
        return self._page.locator(self._sel).all()

    def get(self, index: int) -> Job:
        articles = self._articles()
        if index < 0 or index >= len(articles):
            raise IndexError(
                f"Job index {index} out of range (0–{len(articles) - 1})"
            )
        return Job(articles[index], index)

    def __getitem__(self, index: int) -> Job:
        return self.get(index)

    def __len__(self) -> int:
        return len(self._articles())

    def __iter__(self):
        for i, loc in enumerate(self._articles()):
            yield Job(loc, i)

    # ── bulk helpers ──────────────────────────

    def all(self) -> list[Job]:
        """Return every job card as a list."""
        return list(self)

    def summaries(self) -> list[dict]:
        """Return all cards as a list of dicts (useful for pandas / JSON)."""
        return [job.summary() for job in self]

    def filter(
        self,
        must_have:     Optional[list[str]] = None,
        must_not_have: Optional[list[str]] = None,
        women_only:    Optional[bool]      = None,
        remote_only:   Optional[bool]      = None,
        min_salary_disclosed: bool         = False,
        case_sensitive: bool               = False,
    ) -> list[Job]:
        """
        Return jobs matching all specified criteria.

        Example
        -------
        senior_remote = jobs.filter(must_have=["Python"], remote_only=True)
        """
        results = []
        for job in self:
            card_text = job._full_text()
            if not case_sensitive:
                card_text = card_text.lower()

            # keyword inclusion
            if must_have:
                needles = [k if case_sensitive else k.lower() for k in must_have]
                if not any(n in card_text for n in needles):
                    continue

            # keyword exclusion
            if must_not_have:
                needles = [k if case_sensitive else k.lower() for k in must_not_have]
                if any(n in card_text for n in needles):
                    continue

            if women_only is not None and job.is_women_only() != women_only:
                continue

            if remote_only is not None and job.is_remote() != remote_only:
                continue

            if min_salary_disclosed and not job.is_salary_disclosed():
                continue

            results.append(job)
        return results

    def click_first_matching(
        self,
        must_have:     Optional[list[str]] = None,
        must_not_have: Optional[list[str]] = None,
        case_sensitive: bool = False,
    ) -> Optional[Job]:
        """
        Click the first job that passes keyword conditions.
        Returns the Job that was clicked, or None if none matched.

        Example
        -------
        clicked = jobs.click_first_matching(
            must_have=["Python", "Airflow"],
            must_not_have=["Java"]
        )
        """
        for job in self:
            clicked = job.click_if(
                must_have=must_have,
                must_not_have=must_not_have,
                case_sensitive=case_sensitive,
            )
            if clicked:
                return job
        return None

    def click_all_matching(
        self,
        must_have:     Optional[list[str]] = None,
        must_not_have: Optional[list[str]] = None,
        case_sensitive: bool = False,
    ) -> list[Job]:
        """
        Click every job that passes keyword conditions and return them.
        Useful for bulk-opening tabs or saving jobs programmatically.
        """
        clicked = []
        for job in self:
            if job.click_if(must_have=must_have, must_not_have=must_not_have,
                            case_sensitive=case_sensitive):
                clicked.append(job)
        return clicked

    def __repr__(self) -> str:
        return f"<JobList count={len(self)}>"


# ─────────────────────────────────────────────
#  QUICK DEMO  (run directly: python naukri_jobs.py)
# ─────────────────────────────────────────────

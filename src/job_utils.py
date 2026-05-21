"""
Job Utilities - Strong API for job interactions and queries
Fluent interface for getting job details, filtering, and clicking with conditions
"""

import re
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum
from playwright.sync_api import Page, Locator


class FilterCondition(Enum):
    """Filter condition types"""
    MUST_CONTAIN = "must_contain"      # Keywords that MUST be present
    MUST_NOT_CONTAIN = "must_not_contain"  # Keywords that must NOT be present
    AND = "and"                         # ALL conditions must match
    OR = "or"                           # ANY condition must match


@dataclass
class JobFilter:
    """Job filter with keywords and conditions"""
    keywords: List[str]
    condition: FilterCondition = FilterCondition.MUST_CONTAIN
    case_sensitive: bool = False


class JobDetails:
    """Data class for job details"""
    def __init__(self, element: Locator):
        self.element = element
        self._cache = {}
    
    def _extract_text(self, selector: str, attr: str = "text") -> str:
        """Extract text from element"""
        try:
            if attr == "text":
                return self.element.locator(selector).first.inner_text().strip()
            else:
                return self.element.locator(selector).first.get_attribute(attr).strip()
        except:
            return ""
    
    @property
    def role(self) -> str:
        """Get job role/title"""
        if "role" not in self._cache:
            self._cache["role"] = self._extract_text("a.jobTitle, .job-title, [class*='title']")
        return self._cache["role"]
    
    @property
    def company(self) -> str:
        """Get company name"""
        if "company" not in self._cache:
            self._cache["company"] = self._extract_text(".companyName, .company-name, [class*='company']")
        return self._cache["company"]
    
    @property
    def experience_required(self) -> str:
        """Get experience requirement (e.g., '3-5 Yrs')"""
        if "exp" not in self._cache:
            self._cache["exp"] = self._extract_text("span[title*='Yrs'], [class*='experience']")
        return self._cache["exp"]
    
    @property
    def location(self) -> str:
        """Get job location"""
        if "location" not in self._cache:
            self._cache["location"] = self._extract_text("[class*='location'], .job-location, span[title*='location']")
        return self._cache["location"]
    
    @property
    def salary(self) -> str:
        """Get salary information"""
        if "salary" not in self._cache:
            self._cache["salary"] = self._extract_text("[class*='salary'], .job-salary, span[title*='salary']")
        return self._cache["salary"]
    
    @property
    def job_description(self) -> str:
        """Get job description (JD)"""
        if "jd" not in self._cache:
            self._cache["jd"] = self._extract_text("[class*='jd'], .job-description, [class*='description']")
        return self._cache["jd"][:500]  # First 500 chars
    
    @property
    def skills_required(self) -> List[str]:
        """Get required skills"""
        if "skills" not in self._cache:
            try:
                skills_text = self._extract_text("[class*='skills'], .job-skills, [class*='requirement']")
                # Split by common delimiters
                skills = re.split(r'[,|•\-\n]', skills_text)
                self._cache["skills"] = [s.strip() for s in skills if s.strip()]
            except:
                self._cache["skills"] = []
        return self._cache["skills"]
    
    @property
    def is_urgent_hiring(self) -> bool:
        """Check if urgent hiring"""
        text = (self.role + " " + self.job_description + " " + self.company).lower()
        urgent_keywords = ["urgent", "immediate", "asap", "urgent hiring", "hiring urgently"]
        return any(keyword in text for keyword in urgent_keywords)
    
    @property
    def is_women_only(self) -> bool:
        """Check if women-only job"""
        text = (self.role + " " + self.job_description + " " + self.company).lower()
        women_keywords = ["women", "female", "women only", "female candidates", "women preferred"]
        return any(keyword in text for keyword in women_keywords)
    
    @property
    def is_freshers(self) -> bool:
        """Check if fresher/entry-level position"""
        text = (self.experience_required + " " + self.job_description).lower()
        fresher_keywords = ["fresher", "0 yrs", "entry level", "no experience", "graduate"]
        return any(keyword in text for keyword in fresher_keywords)
    
    def get_experience_range(self) -> tuple:
        """Get experience range as (min_years, max_years)
        Returns: (None, None) if not found, (x, None) for "x+ years"
        """
        exp_text = self.experience_required
        if not exp_text:
            return (None, None)
        
        # Match patterns like "3-5 Yrs", "5+ Yrs", "3 Yrs"
        match = re.search(r'(\d+)\s*(?:-|to)\s*(\d+)', exp_text)
        if match:
            return (int(match.group(1)), int(match.group(2)))
        
        match = re.search(r'(\d+)\s*\+', exp_text)
        if match:
            return (int(match.group(1)), None)
        
        match = re.search(r'(\d+)', exp_text)
        if match:
            return (int(match.group(1)), int(match.group(1)))
        
        return (None, None)
    
    def matches_experience(self, user_experience: float) -> bool:
        """Check if job matches user experience
        Returns True if user_experience is within or close to requirement
        """
        min_exp, max_exp = self.get_experience_range()
        
        if min_exp is None:
            return True
        
        if max_exp is None:
            # "5+ years" - user must have at least min_exp
            return user_experience >= min_exp
        
        # Range: min_exp - max_exp
        # Accept if within range or slightly below
        return user_experience >= min_exp - 1
    
    def contains_keywords(self, keywords: List[str], case_sensitive: bool = False) -> bool:
        """Check if job contains ALL keywords"""
        search_text = self.role + " " + self.company + " " + self.job_description
        if not case_sensitive:
            search_text = search_text.lower()
            keywords = [k.lower() for k in keywords]
        
        return all(keyword in search_text for keyword in keywords)
    
    def excludes_keywords(self, keywords: List[str], case_sensitive: bool = False) -> bool:
        """Check if job does NOT contain any keywords"""
        search_text = self.role + " " + self.company + " " + self.job_description
        if not case_sensitive:
            search_text = search_text.lower()
            keywords = [k.lower() for k in keywords]
        
        return not any(keyword in search_text for keyword in keywords)
    
    def apply_filter(self, job_filter: JobFilter) -> bool:
        """Apply filter to job"""
        if job_filter.condition == FilterCondition.MUST_CONTAIN:
            return self.contains_keywords(job_filter.keywords, job_filter.case_sensitive)
        elif job_filter.condition == FilterCondition.MUST_NOT_CONTAIN:
            return self.excludes_keywords(job_filter.keywords, job_filter.case_sensitive)
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "role": self.role,
            "company": self.company,
            "experience": self.experience_required,
            "location": self.location,
            "salary": self.salary,
            "jd": self.job_description,
            "skills": self.skills_required,
            "is_urgent_hiring": self.is_urgent_hiring,
            "is_women_only": self.is_women_only,
            "is_freshers": self.is_freshers,
        }


class JobList:
    """Strong API for job list operations"""
    
    def __init__(self, page: Page):
        self.page = page
        self.jobs_loc = page.locator("article.jobTuple")
        self._cache = {}
    
    def count(self) -> int:
        """Get total number of jobs"""
        return self.jobs_loc.count()
    
    def get_at_index(self, index: int) -> JobDetails:
        """Get job details at index"""
        if index < 0 or index >= self.count():
            raise IndexError(f"Job index {index} out of range (0-{self.count()-1})")
        
        if index not in self._cache:
            job_element = self.jobs_loc.nth(index)
            self._cache[index] = JobDetails(job_element)
        
        return self._cache[index]
    
    def filter_by_experience(self, user_experience: float) -> List[int]:
        """Get indices of jobs matching user experience"""
        matching_indices = []
        for i in range(self.count()):
            if self.get_at_index(i).matches_experience(user_experience):
                matching_indices.append(i)
        return matching_indices
    
    def filter_by_keywords(self, keywords: List[str], 
                          must_contain: bool = True,
                          case_sensitive: bool = False) -> List[int]:
        """Filter jobs by keywords
        
        Args:
            keywords: List of keywords to search for
            must_contain: If True, ALL keywords must be present. If False, NONE should be present
            case_sensitive: Case sensitive search
        
        Returns:
            List of matching job indices
        """
        matching_indices = []
        for i in range(self.count()):
            job = self.get_at_index(i)
            if must_contain:
                if job.contains_keywords(keywords, case_sensitive):
                    matching_indices.append(i)
            else:
                if job.excludes_keywords(keywords, case_sensitive):
                    matching_indices.append(i)
        return matching_indices
    
    def filter_by_location(self, locations: List[str]) -> List[int]:
        """Filter jobs by location"""
        matching_indices = []
        for i in range(self.count()):
            job = self.get_at_index(i)
            if any(loc.lower() in job.location.lower() for loc in locations):
                matching_indices.append(i)
        return matching_indices
    
    def filter_urgent_hiring(self) -> List[int]:
        """Get all urgent hiring jobs"""
        return [i for i in range(self.count()) if self.get_at_index(i).is_urgent_hiring]
    
    def filter_women_only(self) -> List[int]:
        """Get all women-only jobs"""
        return [i for i in range(self.count()) if self.get_at_index(i).is_women_only]
    
    def filter_freshers(self) -> List[int]:
        """Get all fresher/entry-level jobs"""
        return [i for i in range(self.count()) if self.get_at_index(i).is_freshers]
    
    def filter_combined(self, 
                       user_experience: Optional[float] = None,
                       must_have_keywords: Optional[List[str]] = None,
                       must_not_have_keywords: Optional[List[str]] = None,
                       locations: Optional[List[str]] = None,
                       urgent_only: bool = False,
                       women_only: bool = False,
                       freshers_only: bool = False) -> List[int]:
        """Apply multiple filters combined with AND logic
        
        Args:
            user_experience: Filter by matching experience
            must_have_keywords: Keywords that must be present
            must_not_have_keywords: Keywords that must NOT be present
            locations: Filter by location
            urgent_only: Only urgent hiring jobs
            women_only: Only women-only jobs
            freshers_only: Only fresher jobs
        
        Returns:
            List of matching job indices
        """
        matching_indices = set(range(self.count()))
        
        if user_experience is not None:
            exp_filtered = set(self.filter_by_experience(user_experience))
            matching_indices &= exp_filtered
        
        if must_have_keywords:
            kw_filtered = set(self.filter_by_keywords(must_have_keywords, must_contain=True))
            matching_indices &= kw_filtered
        
        if must_not_have_keywords:
            exclude_filtered = set(self.filter_by_keywords(must_not_have_keywords, must_contain=False))
            matching_indices &= exclude_filtered
        
        if locations:
            loc_filtered = set(self.filter_by_location(locations))
            matching_indices &= loc_filtered
        
        if urgent_only:
            urgent_filtered = set(self.filter_urgent_hiring())
            matching_indices &= urgent_filtered
        
        if women_only:
            women_filtered = set(self.filter_women_only())
            matching_indices &= women_filtered
        
        if freshers_only:
            freshers_filtered = set(self.filter_freshers())
            matching_indices &= freshers_filtered
        
        return sorted(list(matching_indices))
    
    def click_with_conditions(self, 
                             index: int,
                             must_contain: Optional[List[str]] = None,
                             must_not_contain: Optional[List[str]] = None) -> bool:
        """Click job with validation conditions
        
        Args:
            index: Job index to click
            must_contain: Keywords that must be in job (if not present, skip)
            must_not_contain: Keywords that must NOT be in job (if present, skip)
        
        Returns:
            True if clicked, False if skipped due to conditions
        """
        job = self.get_at_index(index)
        
        # Check must_contain
        if must_contain:
            if not job.contains_keywords(must_contain):
                return False
        
        # Check must_not_contain
        if must_not_contain:
            if not job.excludes_keywords(must_not_contain):
                return False
        
        # All conditions passed, click the job
        try:
            job.element.evaluate("el => el.click()")
            return True
        except Exception as e:
            print(f"❌ Click failed: {e}")
            return False
    
    def js_click_with_conditions(self,
                                index: int,
                                must_contain: Optional[List[str]] = None,
                                must_not_contain: Optional[List[str]] = None) -> bool:
        """JS click with validation (better for Naukri)"""
        return self.click_with_conditions(index, must_contain, must_not_contain)
    
    def scroll_to_job(self, index: int) -> None:
        """Scroll job into view"""
        self.get_at_index(index).element.scroll_into_view_if_needed()
    
    def print_job_summary(self, index: int) -> None:
        """Print job summary to console"""
        job = self.get_at_index(index)
        print(f"{'='*60}")
        print(f"🔎 Job #{index}")
        print(f"{'='*60}")
        print(f"📍 {job.company} - {job.role}")
        print(f"📅 Experience: {job.experience_required}")
        print(f"📍 Location: {job.location}")
        print(f"💰 Salary: {job.salary}")
        print(f"🏷️  Skills: {', '.join(job.skills_required[:5])}")
        print(f"🔥 Urgent Hiring: {'Yes' if job.is_urgent_hiring else 'No'}")
        print(f"👩 Women Only: {'Yes' if job.is_women_only else 'No'}")
        print(f"🎓 Freshers: {'Yes' if job.is_freshers else 'No'}")
        print(f"{'='*60}")
    
    def print_all_jobs(self, limit: int = 10) -> None:
        """Print summary of all jobs"""
        count = min(self.count(), limit)
        print(f"\n📋 Total Jobs: {self.count()}")
        print(f"🔍 Showing first {count} jobs:\n")
        
        for i in range(count):
            job = self.get_at_index(i)
            print(f"{i+1}. {job.company:<30} | {job.role:<40} | {job.experience_required}")
        
        if self.count() > limit:
            print(f"\n... and {self.count() - limit} more jobs")


# Example usage functions
def example_usage():
    """Example of how to use JobList and JobDetails"""
    
    # Initialize
    # jobs = JobList(page)
    
    # Get total count
    # total = jobs.count()
    
    # Get single job
    # job = jobs.get_at_index(0)
    # role = job.role
    # company = job.company
    # exp = job.experience_required
    # location = job.location
    # salary = job.salary
    # jd = job.job_description
    # skills = job.skills_required
    
    # Check job properties
    # if job.is_urgent_hiring:
    #     print("Urgent!")
    # if job.is_women_only:
    #     print("Women only")
    # if job.is_freshers:
    #     print("Fresher position")
    
    # Filter jobs
    # matching = jobs.filter_by_experience(2.5)
    # python_jobs = jobs.filter_by_keywords(["python", "django"])
    # exclude_java = jobs.filter_by_keywords(["java"], must_contain=False)
    # bangalore_jobs = jobs.filter_by_location(["bangalore", "bengaluru"])
    # urgent = jobs.filter_urgent_hiring()
    
    # Combined filter
    # results = jobs.filter_combined(
    #     user_experience=2.5,
    #     must_have_keywords=["python"],
    #     must_not_have_keywords=["java", "c++"],
    #     locations=["bangalore"],
    #     urgent_only=False
    # )
    
    # Click with conditions
    # clicked = jobs.click_with_conditions(
    #     index=0,
    #     must_contain=["python"],
    #     must_not_contain=["java"]
    # )
    
    pass


if __name__ == "__main__":
    print("✅ Job utilities module ready")
    print("📖 See example_usage() for API documentation")

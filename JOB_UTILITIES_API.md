# 🏢 Job Utilities API - Complete Guide

Strong, fluent API for interacting with job listings on Naukri.com

## 📚 Classes

### 1. `JobDetails` - Single Job Operations

Get detailed information about a single job.

#### Properties

```python
job = job_list.get_at_index(0)

# Basic Info
job.role              # Get job title/role
job.company           # Get company name
job.location          # Get job location
job.salary            # Get salary info
job.experience_required  # Get experience requirement (e.g., "3-5 Yrs")

# Content
job.job_description   # Get job description (first 500 chars)
job.skills_required   # Get list of required skills

# Special Flags
job.is_urgent_hiring  # Check if urgent hiring
job.is_women_only     # Check if women-only position
job.is_freshers       # Check if fresher/entry-level position
```

#### Methods

```python
# Get experience range
min_exp, max_exp = job.get_experience_range()
# Returns: (3, 5) for "3-5 Yrs"
#          (5, None) for "5+ Yrs"
#          (2, 2) for "2 Yrs"

# Check if matches user experience
matches = job.matches_experience(2.5)
# Returns: True if user_experience is within job requirement

# Check for keywords
has_python = job.contains_keywords(["python", "django"])
# Returns: True if ALL keywords are present

# Check for excluded keywords
no_java = job.excludes_keywords(["java", "c++"])
# Returns: True if NONE of the keywords are present

# Convert to dictionary
data = job.to_dict()
# Returns: {role, company, experience, location, salary, jd, skills, is_urgent_hiring, ...}
```

### 2. `JobList` - Multiple Jobs Operations

Manage and filter entire job list.

#### Properties

```python
jobs = JobList(page)

jobs.count()  # Get total number of jobs
```

#### Methods - Basic Access

```python
# Get single job
job = jobs.get_at_index(0)  # Returns JobDetails object

# Get job summary (printed to console)
jobs.print_job_summary(0)

# Print all jobs
jobs.print_all_jobs(limit=10)

# Scroll to job
jobs.scroll_to_job(0)
```

#### Methods - Filtering

```python
# Filter by experience
matching = jobs.filter_by_experience(2.5)
# Returns: [0, 2, 5, 7] - indices of matching jobs

# Filter by keywords (must contain ALL)
python_jobs = jobs.filter_by_keywords(["python", "django"])
# Returns: [1, 3, 5]

# Filter by keywords (must NOT contain any)
exclude_java = jobs.filter_by_keywords(["java", "c++"], must_contain=False)
# Returns: [0, 2, 4, 6]

# Filter by location
bangalore = jobs.filter_by_location(["bangalore", "bengaluru"])
# Returns: [0, 1, 3, 5]

# Filter special jobs
urgent = jobs.filter_urgent_hiring()
women_only = jobs.filter_women_only()
freshers = jobs.filter_freshers()
```

#### Methods - Advanced Filtering

```python
# Combine multiple filters with AND logic
results = jobs.filter_combined(
    user_experience=2.5,
    must_have_keywords=["python", "django"],
    must_not_have_keywords=["java", "spring"],
    locations=["bangalore", "delhi"],
    urgent_only=False,
    women_only=False,
    freshers_only=False
)
# Returns: [1, 4, 7] - indices matching ALL criteria
```

#### Methods - Clicking with Conditions

```python
# Click job only if conditions are met
clicked = jobs.click_with_conditions(
    index=0,
    must_contain=["python"],          # Must have this keyword
    must_not_contain=["java"]         # Must NOT have this keyword
)
# Returns: True if clicked, False if skipped due to conditions

# Scroll and click
jobs.scroll_to_job(0)
jobs.click_with_conditions(0, must_contain=["python"])
```

## 🔍 Usage Examples

### Example 1: Get Single Job Details

```python
from job_utils import JobList
from conf import MY_EXPERIENCE

jobs = JobList(page)

# Get first job
job = jobs.get_at_index(0)

print(f"Role: {job.role}")
print(f"Company: {job.company}")
print(f"Experience: {job.experience_required}")
print(f"Location: {job.location}")
print(f"Urgent: {job.is_urgent_hiring}")
```

### Example 2: Filter by Experience

```python
# Get all jobs matching user experience
matching = jobs.filter_by_experience(MY_EXPERIENCE)
print(f"Jobs matching {MY_EXPERIENCE} years: {len(matching)}")

for idx in matching:
    job = jobs.get_at_index(idx)
    print(f"  {job.company} - {job.role}")
```

### Example 3: Filter by Keywords

```python
# Python/Django jobs
python_jobs = jobs.filter_by_keywords(["python", "django"])
print(f"Python jobs: {len(python_jobs)}")

# Exclude Java jobs
no_java = jobs.filter_by_keywords(["java"], must_contain=False)
print(f"Non-Java jobs: {len(no_java)}")

# Exclude multiple keywords
exclude = jobs.filter_by_keywords(["java", "c++", "spring"], must_contain=False)
```

### Example 4: Combined Filtering

```python
# Python developer, based in Bangalore, not urgent, junior level
valid_jobs = jobs.filter_combined(
    user_experience=2.5,
    must_have_keywords=["python"],
    must_not_have_keywords=["senior", "lead"],
    locations=["bangalore"],
    urgent_only=False,
    women_only=False,
    freshers_only=False
)

print(f"Valid jobs: {len(valid_jobs)}")
for idx in valid_jobs:
    jobs.print_job_summary(idx)
```

### Example 5: Click with Conditions

```python
# Click only if Python job and not Java
clicked = jobs.click_with_conditions(
    index=0,
    must_contain=["python"],
    must_not_contain=["java"]
)

if clicked:
    print("Job clicked - conditions matched")
else:
    print("Job skipped - conditions not met")
```

### Example 6: Print Jobs and Filter

```python
# Print first 10 jobs
jobs.print_all_jobs(limit=10)

# Get urgent hiring jobs only
urgent = jobs.filter_urgent_hiring()
print(f"Urgent hiring positions: {len(urgent)}")

for idx in urgent:
    job = jobs.get_at_index(idx)
    print(f"🔥 {job.company} - {job.role}")
```

### Example 7: Complex Workflow

```python
# 1. Get all jobs
total = jobs.count()
print(f"Total jobs: {total}")

# 2. Filter to valid candidates
valid = jobs.filter_combined(
    user_experience=2.5,
    must_have_keywords=["python"],
    must_not_have_keywords=["java", "legacy"],
    locations=["bangalore", "delhi"]
)
print(f"Valid jobs: {len(valid)}")

# 3. Apply to first 5
applied = 0
for job_idx in valid[:5]:
    job = jobs.get_at_index(job_idx)
    print(f"\nApplying to: {job.company} - {job.role}")
    
    # Scroll to job
    jobs.scroll_to_job(job_idx)
    
    # Click with conditions
    clicked = jobs.click_with_conditions(
        job_idx,
        must_contain=["python"],
        must_not_contain=["java"]
    )
    
    if clicked:
        # Apply logic here...
        applied += 1

print(f"\nApplied: {applied}")
```

## 🎯 Common Patterns

### Pattern 1: Filter and Iterate

```python
# Find all Python jobs in Bangalore
python_jobs = jobs.filter_by_keywords(["python"])
bangalore = jobs.filter_by_location(["bangalore"])
matching = [idx for idx in python_jobs if idx in bangalore]

for idx in matching:
    job = jobs.get_at_index(idx)
    # Do something with job...
```

### Pattern 2: Smart Application

```python
# Apply to jobs matching criteria, but skip certain types
valid_jobs = jobs.filter_combined(
    user_experience=2.5,
    must_have_keywords=["python"],
    must_not_have_keywords=["manager", "lead"],
)

for idx in valid_jobs:
    # Click only if not senior
    clicked = jobs.click_with_conditions(
        idx,
        must_not_contain=["senior", "principal"]
    )
    
    if clicked:
        # Apply...
        pass
```

### Pattern 3: Reporting

```python
# Generate job report
urgent = jobs.filter_urgent_hiring()
women = jobs.filter_women_only()
freshers = jobs.filter_freshers()

print(f"📊 Job Report:")
print(f"  Total: {jobs.count()}")
print(f"  🔥 Urgent: {len(urgent)}")
print(f"  👩 Women Only: {len(women)}")
print(f"  🎓 Freshers: {len(freshers)}")
```

## 📋 Data Models

### JobDetails.to_dict()

```python
{
    "role": "Senior Python Developer",
    "company": "TechCorp",
    "experience": "3-5 Yrs",
    "location": "Bangalore, India",
    "salary": "12-18 LPA",
    "jd": "We are looking for a senior Python developer...",
    "skills": ["Python", "Django", "PostgreSQL", "Docker"],
    "is_urgent_hiring": True,
    "is_women_only": False,
    "is_freshers": False
}
```

## 🔄 Method Chaining

While not traditional chaining, you can combine operations:

```python
# Get matching jobs
jobs_list = jobs.filter_combined(
    user_experience=2.5,
    must_have_keywords=["python"]
)

# Process first match
if jobs_list:
    first_idx = jobs_list[0]
    job = jobs.get_at_index(first_idx)
    jobs.print_job_summary(first_idx)
    jobs.scroll_to_job(first_idx)
    jobs.click_with_conditions(first_idx, must_contain=["python"])
```

## ⚠️ Error Handling

```python
try:
    job = jobs.get_at_index(999)
except IndexError as e:
    print(f"Job not found: {e}")

# Safe filtering (always returns list, may be empty)
matching = jobs.filter_by_keywords(["nonexistent"])
if matching:
    print(f"Found {len(matching)} jobs")
else:
    print("No matching jobs")
```

## 🚀 Integration with Bot

```python
from job_utils import JobList

# In bot.py
job_list = JobList(page)

# Use utilities to filter and process
valid_jobs = job_list.filter_combined(
    user_experience=MY_EXPERIENCE,
    must_have_keywords=["python"],
    must_not_have_keywords=["java"]
)

for idx in valid_jobs:
    # Click with conditions
    if job_list.click_with_conditions(idx, must_contain=["python"]):
        # Apply logic...
        pass
```

## 📊 Performance Notes

- Caches job details after first access
- All filter operations iterate once through jobs
- `filter_combined()` uses set intersection for efficiency
- Print operations don't cache (always fetch fresh)

## 🎓 API Cheat Sheet

```python
# Count
total = jobs.count()

# Get
job = jobs.get_at_index(0)

# Properties
job.role, job.company, job.location, job.salary, job.experience_required
job.job_description, job.skills_required
job.is_urgent_hiring, job.is_women_only, job.is_freshers

# Methods
job.get_experience_range()
job.matches_experience(2.5)
job.contains_keywords(["python"])
job.excludes_keywords(["java"])
job.to_dict()

# Filtering
jobs.filter_by_experience(2.5)
jobs.filter_by_keywords(["python"])
jobs.filter_by_location(["bangalore"])
jobs.filter_urgent_hiring()
jobs.filter_combined(user_experience=2.5, must_have_keywords=["python"])

# Clicking
jobs.click_with_conditions(0, must_contain=["python"])
jobs.scroll_to_job(0)

# Display
jobs.print_job_summary(0)
jobs.print_all_jobs(limit=10)
```

---

✅ **Comprehensive, production-ready API for job interactions!**

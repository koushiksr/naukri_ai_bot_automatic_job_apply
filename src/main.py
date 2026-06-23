
import os
import sys
import re
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from playwright.sync_api import sync_playwright
from conf import SEARCH_URL, BOT_LOG_FILE, JOB_FILTERS, MY_EXPERIENCE
from core.common import log, SkipJobException
from core.browser import login, wait, save_external_job, MAX_ROUNDS, update_resume_if_needed
from core.apply import apply_job, is_applied, extract_job_details, answer_turn, has_input, get_question, get_chatbot
from core.jobs_handler import JobList, Job
from playwright_stealth import stealth_sync
from ai.engine import get_stats, answer_question
from analytics.csv_logger import CSVLogger
from analytics.bot_statistics import BotStatistics
from analytics.dynamic_dashboard import DynamicDashboard

def main():
        csv_logger = CSVLogger()
        try:
            os.makedirs(os.path.dirname(BOT_LOG_FILE), exist_ok=True)
            if os.path.exists(BOT_LOG_FILE):
                os.remove(BOT_LOG_FILE)
        except:
            pass

        with sync_playwright() as p:
            # Check environment for HEADLESS override (useful for Railway)
            env_headless = os.environ.get('HEADLESS', '').lower() == 'true'
            is_headless = env_headless or getattr(sys.modules.get('conf'), 'HEADLESS', False)

            browser = p.chromium.launch(headless=is_headless, args=['--no-sandbox', '--disable-dev-shm-usage'])
            context = browser.new_context()
            page = context.new_page()
            
            # Apply stealth plugin to avoid Naukri bot detection in headless mode
            if is_headless:
                stealth_sync(page)

            login(page)
            update_resume_if_needed(page)

            log("🌐", f"Loading jobs from {SEARCH_URL}...")
            page.goto(SEARCH_URL)
            wait(page, 6000)
            
            # Scroll down to load more jobs into the DOM
            log("⏬", "Scrolling to load more jobs...")
            for _ in range(5):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                wait(page, 2000)

            # Initialize job utilities
            job_list = JobList(page)
            total_jobs = len(job_list)
            log("📌", f"Found {total_jobs} jobs")

            # Print all jobs summary
            count = min(len(job_list), 1000)
            print(f"\n📋 Total Jobs: {len(job_list)}")
            print(f"🔍 Showing first {count} jobs:\n")
            for i in range(count):
                j = job_list[i]
                print(f"{i+1}. {j.get_company():<30} | {j.get_role():<40} | {j.get_experience()}")
            log("", "")

            # Filter jobs using strong utilities
            log("🔍", "Filtering jobs...")
            must_have = JOB_FILTERS.get("must_have_keywords", [])
            must_not_have = JOB_FILTERS.get("must_not_have_keywords", [])
            women_only = JOB_FILTERS.get("women_only")
            remote_only = JOB_FILTERS.get("remote_only")
        
            # Custom filter for user experience
            def check_exp(job: Job) -> bool:
                exp_str = job.get_experience()
                if not exp_str: 
                    return True
                match = re.search(r'(\d+)\s*(?:-|to)\s*(\d+)', exp_str)
                if match:
                    min_e = int(match.group(1))
                    return MY_EXPERIENCE >= min_e - 1
                match = re.search(r'(\d+)\s*\+', exp_str)
                if match:
                    return MY_EXPERIENCE >= int(match.group(1))
                match = re.search(r'(\d+)', exp_str)
                if match:
                    return MY_EXPERIENCE >= int(match.group(1)) - 1
                return True

            valid_jobs = []
            for job in job_list:
                try:
                    role = job.get_role()
                    role_lower = role.lower()
                    
                    if must_have:
                        if not any(re.search(rf'\b{re.escape(k.lower())}\b', role_lower) for k in must_have):
                            log("⏭️", f"Skipped [{job.index}] {role[:100]}... : Missing 'must_have' keywords in Role")
                            csv_logger.log_skipped(job.get_company(), role, job.get_experience(), job.get_location(), "Missing must_have keywords")
                            job.hide()
                            continue
                            
                    if must_not_have:
                        if any(re.search(rf'\b{re.escape(k.lower())}\b', role_lower) for k in must_not_have):
                            log("⏭️", f"Skipped [{job.index}] {role[:100]}... : Contains 'must_not_have' keywords in Role")
                            csv_logger.log_skipped(job.get_company(), role, job.get_experience(), job.get_location(), "Contains must_not_have keywords")
                            job.hide()
                            continue
                            
                    if women_only:
                        if not job.is_women_only():
                            log("⏭️", f"Skipped [{job.index}] {role[:100]}... : Not a women-only job")
                            csv_logger.log_skipped(job.get_company(), role, job.get_experience(), job.get_location(), "Not a women-only job")
                            job.hide()
                            continue
                    else:
                        if job.is_women_only():
                            log("⏭️", f"Skipped [{job.index}] {role[:100]}... : Women-only job (candidate is male)")
                            csv_logger.log_skipped(job.get_company(), role, job.get_experience(), job.get_location(), "Women-only job (candidate is male)")
                            job.hide()
                            continue
                        
                    if remote_only and not job.is_remote():
                        log("⏭️", f"Skipped [{job.index}] {role[:100]}... : Not a remote job")
                        csv_logger.log_skipped(job.get_company(), role, job.get_experience(), job.get_location(), "Not a remote job")
                        job.hide()
                        continue
                        
                    if not check_exp(job):
                        log("⏭️", f"Skipped [{job.index}] {role[:100]}... : Experience requirement mismatch")
                        csv_logger.log_skipped(job.get_company(), role, job.get_experience(), job.get_location(), "Experience mismatch")
                        job.hide()
                        continue
                        
                    valid_jobs.append(job)
                except Exception as e:
                    log("⏭️", f"Skipped [{job.index}]: Error parsing card - {e}")
            
            log("📊", f"Valid jobs (Config Match + Exp Match): {len(valid_jobs)}")
            log("", "")

            applied = 0
            external = 0
            skipped = 0
            errors = 0

            # Apply to first 5 jobs
            for job in valid_jobs[:5]:
                log("\n" + "="*60, "")
                log("🔎", f"Processing job index {job.index}")
            
                # Re-verify job details to handle dynamic DOM recycling
                current_role = job.get_role()
                if must_have and not any(re.search(rf'\b{re.escape(k.lower())}\b', current_role.lower()) for k in must_have):
                    log("⏭️", f"Skipping {current_role} right before apply (DOM changed, not AI/ML)")
                    continue

                # Print job summary
                print(f"{'='*60}")
                print(f"📍 {job.get_company()} - {current_role}")
                print(f"📅 Experience: {job.get_experience()}")
                print(f"📍 Location: {job.get_location()}")
                print(f"💰 Salary: {job.get_salary()}")
                print(f"🏷️  Skills: {', '.join(job.get_skills()[:5])}")
                print(f"🔥 Urgent Hiring: {'Yes' if job.is_urgent_hiring() else 'No'}")
                print(f"👩 Women Only: {'Yes' if job.is_women_only() else 'No'}")
                print(f"{'='*60}")
            
                job_page = None

                try:
                    # Open in new tab (strictly one by one)
                    with context.expect_page() as new_tab:
                        # Use evaluate to click using JS for reliability
                        job._loc.locator("p.title, a.title").first.evaluate("el => el.click()")
                
                    job_page = new_tab.value
                    job_page.wait_for_load_state("domcontentloaded")
                    wait(job_page, 3000)

                    # Check for external redirect
                    if "naukri.com" not in job_page.url:
                        log("🏢", "External company site!")
                    
                        job_data = extract_job_details(job_page)
                        job_data["company"] = job.get_company()
                        job_data["role"] = job.get_role()
                        save_external_job(job_data)
                        external += 1
                        
                        csv_logger.log_external(job.get_company(), job.get_role(), job.get_experience(), job.get_location(), job_page.url)
                    
                        job_page.close()
                        wait(page, 1000)
                        continue

                    # Apply
                    res, data = apply_job(job_page)
                    if res is True:
                        applied += 1
                        log("🎉", f"APPLIED! ({applied})")
                        csv_logger.log_applied(job.get_company(), job.get_role(), job.get_experience(), job.get_location(), data)
                    elif res == "External":
                        external += 1
                        log("🔗", "External application redirected")
                        csv_logger.log_external(job.get_company(), job.get_role(), job.get_experience(), job.get_location(), data)
                    else:
                        log("❌", "Failed")
                        csv_logger.log_skipped(job.get_company(), job.get_role(), job.get_experience(), job.get_location(), f"Application Failed (Answered {data} questions)")

                except SkipJobException as e:
                    log("⏭️", f"Skipped job: {e}")
                    skipped += 1
                except Exception as e:
                    log("💥", f"Error: {e}")
                    errors += 1

                finally:
                    # Ensure the tab is always closed before moving to the next job
                    # This guarantees we only have one application tab open at a time
                    if job_page and not job_page.is_closed():
                        job_page.close()
                        log("🚫", "Closed Job Tab")
                    wait(page, 1000)

            # Print final stats
            log("\n" + "="*60, "")
            log("🏁", f"DONE - Applied: {applied} | External: {external} | Skipped: {skipped} | Errors: {errors}")
            
            stats = get_stats()
            print(f"\n📊 AI Backend Statistics:")
            print(f"   Total Questions: {stats['total_calls']}")
            print(f"   Cached Answers: {stats['cached_answers']}")
            print(f"   Generated Answers: {stats['generated_answers']}")
            print(f"   Gemini Used: {stats['gemini_used']}")
            print(f"   Cache Hit Rate: {stats['cache_hit_rate']:.1%}")
            
            # Record statistics for dashboard
            run_data = {
                'jobs_loaded': total_jobs,
                'jobs_filtered': len(valid_jobs),
                'jobs_applied': applied,
                'jobs_skipped': skipped,
                'questions_total': stats['total_calls'],
                'questions_answered': stats['generated_answers'] + stats['cached_answers'],
                'questions_unanswered': 0,
                'questions_by_type': {},
                'external_redirects': external,
                'external_urls': [],
                'llm_calls': stats['gemini_used'],
                'decision_tree_calls': stats['cached_answers'],
                'cache_hits': stats['cached_answers'],
                'errors': errors,
                'error_list': [],
                'duration': 0,
            }
            
            try:
                bot_stats = BotStatistics()
                bot_stats.record_run(run_data)
                dashboard = DynamicDashboard()
                dashboard.generate_dynamic_dashboard()
                print(f"\n✅ Statistics recorded and dashboard updated!")
                print(f"   View dashboard: data/dashboard.html")
            except Exception as e:
                print(f"⚠️  Could not update dashboard: {e}")


if __name__ == "__main__":
    main()

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.naukri.com/machine-learning-jobs?k=machine%20learning&sortBy=date", timeout=60000)
    page.wait_for_timeout(5000)
    print("Found 'article':", page.locator("article").count())
    print("Found 'article.jobTuple':", page.locator("article.jobTuple").count())
    print("Found '.jobTuple':", page.locator(".jobTuple").count())
    print("Found '.srp-jobtuple-wrapper':", page.locator(".srp-jobtuple-wrapper").count())
    print("Found 'div[class*=\"jobTuple\"]':", page.locator("div[class*='jobTuple']").count())
    browser.close()

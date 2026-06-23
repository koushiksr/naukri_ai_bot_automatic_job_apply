from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.naukri.com/machine-learning-jobs?k=machine%20learning&sortBy=date", timeout=60000)
    page.wait_for_timeout(5000)
    print("Page Title:", page.title())
    print("All 'a' elements with class containing 'title':", len(page.locator("a[class*='title']").all()))
    browser.close()

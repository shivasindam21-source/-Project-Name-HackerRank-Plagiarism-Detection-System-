from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient
import time
import sys

# --- Get username, password, contest from command line ---
username = sys.argv[1]
password = sys.argv[2]
contest = sys.argv[3]

# --- MongoDB setup ---
client = MongoClient("mongodb://localhost:27017/")  # adjust if needed
db = client["Contests"]
collection = db["codes"]

# --- Selenium setup ---
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # optional, avoids bot detection

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)
wait = WebDriverWait(driver, 40)

# --- LOGIN ---
driver.get("https://www.hackerrank.com/auth/login")

# Wait for username input
username_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
username_input.clear()
username_input.send_keys(username)

# Wait for password input
password_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
password_input.clear()
password_input.send_keys(password)

# Wait for login button to be visible and scroll into view
login_button = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "button[type='submit']")))
driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
time.sleep(1)  # small pause to ensure button is ready
login_button.click()

# Wait for page to load
wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
time.sleep(2)

# --- OPEN CONTEST SUBMISSIONS IN NEW TAB ---
driver.execute_script("window.open('');")
driver.switch_to.window(driver.window_handles[1])
driver.get(f"https://www.hackerrank.com/contests/{contest}/judge/submissions/challenge")
wait.until(EC.presence_of_element_located((By.CLASS_NAME, "judge-submissions-list-view")))
time.sleep(2)

# --- GET TEAM NAMES AND LANGUAGES ---
team_elements = driver.find_elements(By.CSS_SELECTOR, "a.challenge-slug.backbone")
lang_elements = driver.find_elements(By.CSS_SELECTOR, "div.judge-submissions-list-view div.span2.submissions-title p.small")

team_names = [team_elements[i].text for i in range(1, len(team_elements), 2)]
languages = [lang_elements[i].text for i in range(0, len(lang_elements), 2)]

# --- GET ALL CODES ---
codes = []
submission_count = len(team_names)
for i in range(submission_count):
    view_button = driver.find_element(
        By.XPATH,
        f'(//div[contains(@class,"judge-submissions-list-view")]//a[contains(@class,"view-results")])[{i+1}]'
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", view_button)
    time.sleep(0.5)  # small pause before click
    view_button.click()

    wait.until(EC.presence_of_element_located(
        (By.XPATH, '//*[@id="submission-code"]/div/div[6]/div[1]/div/div/div/div[5]')
    ))
    code_element = driver.find_element(By.XPATH, '//*[@id="submission-code"]/div/div[6]/div[1]/div/div/div/div[5]')
    codes.append(code_element.text)

    driver.back()
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "judge-submissions-list-view")))
    time.sleep(1)

# --- STORE IN MONGODB ---
for team, lang, code in zip(team_names, languages, codes):
    doc = {
        "teamname": team,
        "lang": lang,
        "copiedfrom": "own",
        "code": code
    }
    collection.insert_one(doc)

driver.quit()
print("All submissions inserted into MongoDB successfully!")

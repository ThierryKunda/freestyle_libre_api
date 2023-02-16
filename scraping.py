import os

from random import randint, random
import time

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import JavascriptException, MoveTargetOutOfBoundsException

edge_options = Options()
edge_options.add_experimental_option("detach", True)
driver = webdriver.Edge(options=edge_options)
driver.implicitly_wait(30)
driver.get("https://www.libreview.com")
driver.execute_script("document.querySelector('#truste-consent-close').click()")

country_select_element, lang_select_element = driver.find_elements(By.TAG_NAME, "select")
country_select = Select(country_select_element)
country_select.select_by_visible_text('France')
lang_select = Select(lang_select_element)
lang_select.select_by_visible_text('Français')
driver.execute_script("document.querySelector('#submit-button').click()")
submit_button = driver.find_element(By.ID, "submit-button")

# Authentification page

email_field, password_field = driver.find_elements(By.TAG_NAME, "input")
email_field.clear()
email_field.send_keys("kundathierry@gmail.com")
email_field.clear()
password_field.send_keys("Jt2p6yc0Mq!BOlw&fE0Kr6_7.:~!")
password_field.send_keys(Keys.RETURN)

# Send SMS code

send_code_btn = driver.find_element(By.ID, "twoFactor-step1-next-button")
send_code_btn.click()
os.system("clear")
code = input("Enter your code : ")
code_input_field = driver.find_element(By.ID, "twoFactor-step2-code-input")
code_input_field.send_keys(code)
check_and_send_btn = driver.find_element(By.ID, "twoFactor-step2-next-button")
check_and_send_btn.click()

# Located at home page
time.sleep(3)
export_data_overlay_button = driver.find_element(By.ID, "exportData-button")
export_data_overlay_button.click()

# reCAPTCHA overlay
time.sleep(1)
click_done = False
captcha = driver.find_element
actions = ActionChains(driver)
actions.move_to_element_with_offset(driver.find_element(By.TAG_NAME, 'body'), 15,0)
actions.move_to_element_with_offset(driver.find_element(By.TAG_NAME, 'body'), 18,3)
actions.move_to_element_with_offset(driver.find_element(By.TAG_NAME, 'body'), 0,0)
actions.move_by_offset(11, 22.5).click().perform()
captcha_size = (50, 50)
for i in range(20):
    x = random()*10
    y = random()*10
    print("x = ", x, "y = ", y)
    try:
        actions.move_by_offset(x,y).click().perform()
    except MoveTargetOutOfBoundsException:
        pass
    time.sleep(0.1)
for i in range(0, 20):
    for j in range(10, 15):
        try:
            print(i,j,sep=' ')
            actions.move_by_offset(i,j).click().perform()
        except MoveTargetOutOfBoundsException:
            print("Out of bounds")

# captcha_checkbox = driver.find_element(By.CLASS_NAME, "recaptcha-checkbox-border")
# download_btn = driver.find_element(By.ID, "exportData-modal-download-button")
# download_btn.click()
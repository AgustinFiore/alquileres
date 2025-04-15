from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller
import hashlib
import os
import requests
import subprocess
import time

MAX_RETRIES = 3

def process_url(url: str, file_name: str):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)

    dictionary = construct_dict(file_name)
    total_saved = len(dictionary)

    wait = WebDriverWait(driver, 10)
    continue_loop = True

    while continue_loop:
        try:
            elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@class, 'prop-title')]")))
        except Exception:
            driver.quit()
            return

        for elem in elements:
            for retry_number in range(MAX_RETRIES):
                try:
                    text = driver.execute_script("return arguments[0].innerText;", elem)
                    href = elem.get_attribute("href") or ""
                except StaleElementReferenceException as exc:
                    time.sleep(0.2)
                    if retry_number + 1 >= MAX_RETRIES:
                        raise exc
            hash = get_hash(text)
            if dictionary.get(hash) is None:
                send_telegram_message(text + ": " + href)
            dictionary[hash] = True

        try:
            new_elem = driver.find_element(By.XPATH, "//a[contains(@class, 'page-next')]")
            driver.execute_script("arguments[0].click();", new_elem)
            time.sleep(1)
        except NoSuchElementException:
            continue_loop = False

    any_false = any(value == False for value in dictionary.values())
    true_keys = [key for key, value in dictionary.items() if value]
    if any_false or len(true_keys) > total_saved:
        file = open(file_name, 'w')
        for true_hash in true_keys:
            file.write(true_hash + "\n")
        file.close()
        commit_and_push(file_name)
    driver.quit()

def commit_and_push(file_name: str):
    email = os.getenv('EMAIL')
    username = os.getenv('USERNAME')
    subprocess.run(["git", "config", "--global", "user.email", email])
    subprocess.run(["git", "config", "--global", "user.name", username])
    subprocess.run(["git", "add", file_name])
    subprocess.run(["git", "commit", "-m", f"Update {file_name}"])
    subprocess.run(["git", "push"])

def get_hash(text: str):
    hash_object = hashlib.sha256()
    hash_object.update(text.encode())
    return hash_object.hexdigest()

def construct_dict(file_name: str):
    file = open(file_name, 'r')
    dictionary = {}
    for line in file:
        dictionary[line.strip()] = False
    file.close()

    return dictionary

def send_telegram_message(message: str):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    return response

def main():
    url_duplex = 'https://www.bahiablancapropiedades.com/buscar#duplex/alquiler/bahia-blanca/todos-los-barrios/por-defecto/mapa=1'
    url_dpto_tres = 'https://www.bahiablancapropiedades.com/buscar#departamentos/alquiler/bahia-blanca/todos-los-barrios/por-defecto/mapa=1;dormitorios=3_dormitorios'
    url_casa_tres = 'https://www.bahiablancapropiedades.com/buscar#departamentos/fideicomiso/bahia-blanca/todos-los-barrios/por-defecto/mapa=1'
    file_name_duplex = 'duplex_hash.txt'
    file_name_dpto_tres = 'dpto_tres_hash.txt'
    file_name_casa_tres = 'casa_tres_hash.txt'
    chromedriver_autoinstaller.install()
    process_url(url_duplex, file_name_duplex)
    process_url(url_dpto_tres, file_name_dpto_tres)
    process_url(url_casa_tres, file_name_casa_tres)

if __name__ == "__main__":
    main()

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import chromedriver_autoinstaller
import os
import requests
import subprocess
import time

def get_html(url: str, file_name: str):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no browser window)
    driver = webdriver.Chrome(options=chrome_options)

    driver.get(url)
    file = open(file_name, 'r')
    content = file.readline()
    old_count = int(content)
    file.close()

    time.sleep(5) # Wait for JavaScript to execute and load content
    try:
        element = driver.find_element(By.XPATH, '//*[@id="search-results"]/div[1]/div/div/div[1]/div[1]/div[1]/div[1]/span[2]')
    except NoSuchElementException:
        driver.quit()
        return
    text = element.text
    i = 0
    count = ""
    loop = True
    while loop:
        if text[i] != " ":
            count += text[i]
            i += 1
        else:
            loop = False

    cant_duplex = int(count)
    if cant_duplex > old_count:
        write_file(count, file_name)
        old_count = int(count)
        if file_name == "duplex.txt":
            send_telegram_message(f"Nuevo duplex publicado: {url}")
        else:
            send_telegram_message(f"Nuevo dpto de 3 dormitorios publicado: {url}")
    elif cant_duplex < old_count:
        write_file(count, file_name)
        old_count = int(count)
    driver.quit()

def write_file(value: str, file_name: str):
    file = open(file_name, 'w')
    file.truncate(0)
    file.write(value)
    file.close()
    commit_and_push(file_name)

def commit_and_push(file_name: str):
    subprocess.run(["git", "config", "--global", "user.email", "fiore_agustin@hotmail.com"])
    subprocess.run(["git", "config", "--global", "user.name", "AgustinFiore"])
    subprocess.run(["git", "add", file_name])
    subprocess.run(["git", "commit", "-m", f"Update {file_name}"])
    subprocess.run(["git", "push"])

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
    file_name_duplex = 'duplex.txt'
    file_name_dpto_tres = 'dpto_tres.txt'
    chromedriver_autoinstaller.install()
    get_html(url_duplex, file_name_duplex)
    get_html(url_dpto_tres, file_name_dpto_tres)

if __name__ == "__main__":
    main()

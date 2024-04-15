from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import json
import m3u8
import requests
import os
import subprocess
driver = webdriver.Chrome()  # or webdriver.Firefox()

def filterUnavailable(element):
    try:
        element.find_element(By.CLASS_NAME,"label-auth")
        return False
    except:
        return True
def seasonMap(season):
    return season.find_element(By.CSS_SELECTOR,"a").get_attribute("href")
def getSeasons():
    driver.get(f"https://www.southparkstudios.com/seasons/south-park")
    seasonList = driver.find_element(By.CSS_SELECTOR,'div[data-display-name="SeasonSelector"]').find_element(By.CSS_SELECTOR,"ul").find_elements(By.CSS_SELECTOR,"li")
    return list(map(seasonMap,seasonList))[::-1]
def add_zero_to_numbers(string):
    parts = string.split()
    if len(parts) == 4 and parts[0] == "Season" and parts[2] == "E":
        season_number = parts[1]
        episode_number = parts[3]

        season_number = season_number.zfill(2)

        episode_number = episode_number.zfill(2)
        return f"S{season_number}E{episode_number}"
    else:
        return "Invalid format"
def getEpisodes(href):
    driver.get(href)
    try:
        driver.find_element(By.CLASS_NAME,"btn").click()
    except:
        pass
    finally:
        time.sleep(3)
    episodes = driver.find_element(By.ID,"content-full-episodes-season").find_elements(By.CSS_SELECTOR,"li")
    episodes = list(filter(filterUnavailable,episodes))
    return list(map(seasonMap,episodes))
seasons = getSeasons()
start = abs(int(input("Start season: ")))
end = abs(int(input("End season: ")))
if(start > len(seasons) or end > len(seasons) or start == 0 or end == 0):
    print("invalid season input")
else:
    for i in range(start,end+1):
        episodes = getEpisodes(seasons[i-1])
        for episode in episodes:
            driver.get(episode)
            data = driver.find_element(By.CSS_SELECTOR, 'div[data-display-name="PlayerMetadata"]').find_elements(By.CSS_SELECTOR,"p")
            title = data[0].get_attribute("innerText")
            episode = add_zero_to_numbers(data[1].get_attribute("innerText").split("•")[0])
            element = False
            timeout = 5
            while not element:
                try:
                    element = WebDriverWait(driver, timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'video'))
                    )
                except TimeoutException:
                    print("Element not found within the specified timeout period")
            master = False
            while not master:
                try:
                    driver.find_element(By.CSS_SELECTOR,'avia-button[loc-id="play"]').click()
                except:
                    pass
                JS_get_network_requests = """
                var performance = window.performance || window.msPerformance || window.webkitPerformance || {};
                var network = performance.getEntries() || {};
                return JSON.stringify(network);
                """
                network_requests = json.loads(driver.execute_script(JS_get_network_requests))
                masterLink = ""
                for n in network_requests:
                    if "master.m3u8" in n["name"]:
                        master = n["name"]
                time.sleep(2)
            r = requests.get(master)
            m3u8_master = m3u8.loads(r.text)
            command = f'ffmpeg -y -i "{master}" -map 0:p:{len(m3u8_master.data["playlists"])-1} -c copy video.ts'
            subprocess.run(command, shell=True)
            subprocess.run(f'ffmpeg -y -i video.ts -c copy "South Park {episode} - {title}.mp4"',shell=True)
            os.unlink("video.ts")

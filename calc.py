from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from rank_map import Rank_map

def scrape_matches_with_selenium():
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
    URL = "https://csstats.gg/player/" + input("Enter the URL of the player's stats page: https://csstats.gg/player/")

    # If URL is pasted from site, remove the site URL
    if URL.startswith("https://csstats.gg/player/https://csstats.gg/player/"):
        URL = URL.replace("https://csstats.gg/player/https://csstats.gg/player/", "https://csstats.gg/player/")

    driver.get(URL)

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "usercentrics-root"))
        )
        # Remove cookie banner
        driver.execute_script("""
            var element = document.getElementById('usercentrics-root');
            if (element) {
                element.parentNode.removeChild(element);
            }
        """)

        # Go to matches tab
        matches_tab = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//span[@onclick=\"content_tab('matches');\"]"))
        )
        matches_tab.click()

        # Wait for matches to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#match-list-outer > table > tbody > tr"))
        )

        # Iterate over matches to find the rank_up game
        matches = driver.find_elements(By.CSS_SELECTOR, "#match-list-outer > table > tbody > tr")
        rank_up_index = None
        rank_up_date = None
        results = []

        for idx, match in enumerate(matches):
            if match.find_elements(By.CLASS_NAME, "glyphicon-chevron-up"):
                date_element = match.find_element(By.CSS_SELECTOR, "td:nth-child(1)")
                rank_up_date = date_element.get_attribute('innerText').strip()
                rank_up_date = time.strftime("%d/%m/%y", time.strptime(rank_up_date, "%a %dth %b %y"))
                rank_up_index = idx
                result_span = match.find_element(By.CSS_SELECTOR, "td:nth-child(5) > span")                
                # Get background image from class
                background_image = driver.execute_script("""
                    var element = arguments[0];
                    var style = window.getComputedStyle(element);
                    return style.getPropertyValue('background-image');
                """, result_span)
                if background_image:
                    background_image_url = background_image.split('"')[1]
                    rank = Rank_map.rank_map.get(background_image_url, "Unknown Rank")
                    break

        if rank_up_index is None:
            raise Exception("No rank_up game found.")

        for match in matches[:rank_up_index]:
            # Parse match result based on the color of the result
            result_span = match.find_element(By.CSS_SELECTOR, "td:nth-child(4) > span")
            color = result_span.value_of_css_property("color")

            if color == "rgb(150, 198, 38)":  # Win color
                results.append("Win")
            elif color == "rgb(160, 65, 65)":  # Loss color
                results.append("Loss")
            elif color == "rgb(34, 126, 202)":  # Tie color
                results.append("Tie")

        wins = results.count("Win")
        losses = results.count("Loss")
        ties = results.count("Tie")

        current_win_streak = 0
        for result in results:
            if result == "Win":
                current_win_streak += 1
            else:
                break

        return wins, losses, ties, rank_up_date, current_win_streak, rank

    finally:
        driver.quit()

if __name__ == "__main__":
    wins, losses, ties, rank_up_date, current_win_streak, rank = scrape_matches_with_selenium()
    print(f"Since Rank Up to {rank} on {rank_up_date}:")
    print(f"Wins: {wins}, Losses: {losses}, Ties: {ties}")
    print(f"Current win streak: {current_win_streak}")

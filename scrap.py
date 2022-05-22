import datetime
import json

import pdfkit
from jinja2 import Environment, FileSystemLoader
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


def get_today_and_str():
    today = datetime.date.today()
    today_str = today.strftime("%Y/%m/%d")
    return (today, today_str)

def get_next_day_and_str(today):
    next_day = today + datetime.timedelta(days=1)
    next_day_str = next_day.strftime("%Y/%m/%d")
    return (next_day, next_day_str)

def scrap_webpage(url, day):
    browser = webdriver.Chrome(ChromeDriverManager().install())
    browser.get(url)

    devotional_dict = {}

    try:
        wait = WebDriverWait(browser, 15)
        element = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "container"))
        )

        date = element.find_element(By.CSS_SELECTOR, "html body div#root div.App main div div.content-wrap div div.container div.sticky-parent div.calendar-toggle").text
        devotional_dict["day"] = day
        devotional_dict["date"] = date
        title = element.find_element(By.CLASS_NAME, "devo-title").text
        devotional_dict["title"] = title
        passage = element.find_element(By.CLASS_NAME, "verseArea").text
        devotional_dict["passage"] = passage
        verse = element.find_element(By.CLASS_NAME, "skipRefTagger")
        verse_text = verse.text
        verse_link = verse.get_attribute("href")
        devotional_dict["verse_text"] = verse_text
        devotional_dict["verse_link"] = verse_link

        content = element.find_element(By.CLASS_NAME, "content")
        content_elements = content.find_element(By.TAG_NAME, "div").find_elements(By.TAG_NAME, "p")
        for content in content_elements:
            devotional_dict.setdefault("content", []).append(content.text)

        author = element.find_element(By.CLASS_NAME, "devo-author").find_element(By.TAG_NAME, "span").find_element(By.TAG_NAME, "a")
        author_text = author.text
        author_link = author.get_attribute("href")
        devotional_dict["author_text"] = author_text
        devotional_dict["author_link"] = author_link

        reflection_heading = element.find_element(By.CLASS_NAME, "devo-prayer-heading").text
        devotional_dict["reflection_heading"] = reflection_heading
        reflection_question = element.find_element(By.CLASS_NAME, "devo-question").text
        devotional_dict["reflection_question"] = reflection_question
        reflection_prayer = element.find_element(By.CLASS_NAME, "devo-prayer").text
        devotional_dict["reflection_prayer"] = reflection_prayer

    finally:
        browser.quit()
    return devotional_dict


if __name__ == "__main__":
    template_loader = FileSystemLoader(searchpath="./templates")
    env = Environment(loader=template_loader)
    template = env.get_template("devotional.html.j2")

    # Get day
    days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    (today, today_str) = get_today_and_str()
    next_day = today
    (next_day, nextday_str) = get_next_day_and_str(next_day)
    devotionals = []
    for day in days:
        (next_day, nextday_str) = get_next_day_and_str(next_day)
        url = 'https://nuestropandiario.org/CR/{nextday_str}'.format(nextday_str=nextday_str)
        devotional_dict = scrap_webpage(url, day)
        devotionals.append(devotional_dict)

    with open("devotional-week.html", mode="w+") as file:
        file.write(template.render({'devotionals': devotionals}))

    pdfkit.from_file('devotional-week.html', 'devotional-week.pdf')

# Issue with links. https://github.com/wkhtmltopdf/wkhtmltopdf/issues/4406#issuecomment-955987766
# It is only available for Windows

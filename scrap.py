import datetime
import os
import re
import sys
from argparse import ArgumentParser
from typing import Dict, List, Tuple

import urllib.parse

from jinja2 import Environment, FileSystemLoader

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.chrome.service import Service
from weasyprint import HTML, CSS
# from webdriver_manager.chrome import ChromeDriverManager

scrap_timeout_seconds = 60
main_parser = ArgumentParser()
subparsers = main_parser.add_subparsers(dest="subcommand")

template_loader = FileSystemLoader(searchpath="./templates")
env = Environment(loader=template_loader)
template = env.get_template("devotional.html.j2")
build_path = "./build"


def makedir_helper(new_path: str) -> bool:
    if not os.path.isdir(new_path):
        try:
            os.makedirs(new_path)
        except OSError as error:
            print(
                "Could not create dir %s\n%s", new_path, error
            )
            sys.exit(1)
    else:
        print("Skipping, already created dir %s", new_path)
    return os.path.isdir(new_path)

def argument(*name_or_flags, **kwargs):
    """Convenience function to properly format arguments to pass to the
    subcommand decorator.
    """
    return (list(name_or_flags), kwargs)


def subcommand(args=[], parent=subparsers):
    """Decorator to define a new subcommand in a sanity-preserving way.
    The function will be stored in the ``func`` variable when the parser
    parses arguments so that it can be called directly like so::
        args = cli.parse_args()
        args.func(args)
    Usage example::
        @subcommand([argument("-d", help="Enable debug mode", action="store_true")])
        def subcommand(args):
            print(args)
    Then on the command line::
        $ python cli.py subcommand -d
    """

    def decorator(func):
        parser = parent.add_parser(func.__name__, description=func.__doc__)
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
        parser.set_defaults(func=func)

    return decorator


def get_month_str(p_date: datetime.date) -> str:
    months : List[str] = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Setiembre", "Octubre", "Noviembre", "Diciembre"]
    month : int = p_date.month - 1
    return months[month]


def get_weekday_str(p_date: datetime.date) -> str:
    weekdays : List[str] = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    weekday : int = p_date.weekday()
    return weekdays[weekday]


def get_current_and_str(p_current_str: str) -> Tuple[datetime.date, str]:
    current : datetime.date = datetime.date.fromisoformat(p_current_str)
    current_str : str = current.strftime("%Y/%m/%d")
    return (current, current_str)


def get_today_and_str() -> Tuple[datetime.date, str]:
    today = datetime.date.today()
    today_str = today.strftime("%Y/%m/%d")
    return (today, today_str)


def get_next_day_and_str(today) -> Tuple[datetime.date, str]:
    next_day = today + datetime.timedelta(days=1)
    next_day_str = next_day.strftime("%Y/%m/%d")
    return (next_day, next_day_str)


def add_references(text) -> str:
    new_text = text
    books_and_ref_groups = [['Génesis', 'Gn', 'Gén'], ['Nahúm', 'Nah', 'Na'], ['Éxodo', 'Ex'], ['Habacuc', 'Hab', 'Ha'], ['Levítico', 'Lv', 'Lev'], ['Sofonías', 'Sof', 'So'], ['Números', 'Nm', 'Núm'], ['Hageo', 'Ageo', 'Hag', 'Ag'], ['Deuteronomio', 'Dt'], ['Zacarías', 'Zac', 'Za'], ['Josué', 'Jos'], ['Malaquías', 'Mal', 'Ml'], ['Jueces', 'Jue', 'Jc'], ['Mateo', 'Mt', 'Mat'], ['Rut', 'Rt', 'Rut'], ['Marcos', 'Mc', 'Mr', 'Mar'], ['1 Samuel', '1 S', '1 Sam'], ['2 Samuel', '2 S', '2 Sam'], ['1 Reyes', '1 R', '1 Rey'], ['2 Reyes', '2 R', '2 Rey'], ['Lucas', 'Lc', 'Luc'], ['Juan', 'Jn', 'Juan'], ['Hechos', 'Hch', 'He', 'Hech'], ['Romanos', 'Rom', 'Ro', 'Rm'], ['1 Crónicas', '1 Cr', '1 Cro', '1 Cró', '1 Crón'], ['1 Corintios', '1 Co', '1 Cor'], ['2 Crónicas', '2 Cr', '2 Cro', '2 Cró', '2 Crón'], ['2 Corintios', '2 Co', '2 Cor'], ['Esdras', 'Esd'], ['Gálatas', 'Ga', 'Gál', 'Gá', 'Gl'], ['Nehemías', 'Neh', 'Ne'], ['Efesios', 'Ef'], ['Ester', 'Est'], ['Filipenses', 'Fil', 'Flp'], ['Job', 'Job', 'Jb'], ['Colosenses', 'Col'], ['Salmo', 'Salmos', 'Sal', 'Sl'], ['1 Tesalonicenses', '1 Tls', '1 Tes', '1 Te'], ['Proverbios', 'Pr', 'Prv', 'Pro'], ['2 Tesalonicenses', '2 Tls', '2 Tes', '2 Te'], ['Eclesiastés', 'Ec'], ['1 Timoteo', '1 Tim', '1 Ti', '1 Tm'], ['Cantares', 'Cnt', 'Ct', 'Cant'], ['2 Timoteo', '2 Tim', '2 Ti', '2 Tm'], ['Isaías', 'Is', 'Isa'], ['Tito', 'Tit', 'Ti', 'Tt'], ['Jeremías', 'Jer', 'Jr'], ['Filemón', 'Flm', 'Filem'], ['Lamentaciones', 'Lm', 'Lam'], ['Hebreos', 'Heb', 'He', 'Hb'], ['Ezequiel', 'Ez', 'Ezq'], ['Santiago', 'St', 'Sant', 'Stg', 'Stgo'], ['Daniel', 'Dn', 'Dan'], ['1 Pedro', '1 P', '1 Pe', '1 Ped'], ['Oseas', 'Os'], ['2 Pedro', '2 P', '2 Pe', '2 Ped'], ['Joel', 'Jl', 'Joel'], ['1 Juan', '1 Jn'], ['Amós', 'Am'], ['2 Juan', '2 Jn'], ['Abdías', 'Abd', 'Ab'], ['3 Juan', '3 Jn'], ['Jonás', 'Jon'], ['Judas', 'Jud', 'Jds'], ['Miqueas', 'Miq', 'Mi'], ['Apocalipsis', 'Ap', 'Apoc']]
    books = [book_group[0] for book_group in books_and_ref_groups]
    pattern = re.compile(r'(\(.*?\))') # verse in reference is enclosed in parenthesis
    link = "<a href=\"{verse_link}\" style=\"font-family: Serif !important; font-size: 20px; text-align: center; color: rgb(9, 50, 93); text-decoration: none;\"> {verse_text}</a>"
    for match in pattern.finditer(text):
        reference = match.group(1)
        if any([book in reference for book in books]):
            verse_text = reference.replace('(', '').replace(')', '')
            verse_text_quoted = urllib.parse.quote_plus(verse_text.replace(',', ';'))
            verse_link = "https://www.biblegateway.com/passage/?search={verse_text_quoted}&version=RVR1960".format(verse_text_quoted=verse_text_quoted)
            new_text = new_text.replace(verse_text, str(link).format(verse_link=verse_link, verse_text=verse_text))
    return new_text

def scrap_webpage(url, day) -> Dict:
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    browser = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    # browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    browser.get(url)

    devotional_dict : Dict = {}

    try:
        wait = WebDriverWait(browser, scrap_timeout_seconds)
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
        verse_text_quoted = urllib.parse.quote_plus(verse_text.replace(',', ';'))
        verse_link = "https://www.biblegateway.com/passage/?search={verse_text_quoted}&version=RVR1960".format(verse_text_quoted=verse_text_quoted)
        devotional_dict["verse_text"] = verse_text
        devotional_dict["verse_link"] = verse_link

        content = element.find_element(By.CLASS_NAME, "content")
        content_elements = content.find_element(By.TAG_NAME, "div").find_elements(By.TAG_NAME, "p")
        for content in content_elements:
            content_text = add_references(content.text)
            devotional_dict.setdefault("content", []).append(content_text)

        author_text = ""
        author_link = ""
        try:
            author = element.find_element(By.CLASS_NAME, "devo-author").find_element(By.TAG_NAME, "span").find_element(By.TAG_NAME, "a")
            author_text = author.text
            author_link = author.get_attribute("href")
        except Exception as e:
            author_text = ""
            author_link = ""

        devotional_dict["author_text"] = author_text
        devotional_dict["author_link"] = author_link

        reflection_heading = ""
        try:
            reflection_heading = element.find_element(By.CLASS_NAME, "devo-prayer-heading").text
        except Exception as e:
            reflection_heading = ""

        devotional_dict["reflection_heading"] = reflection_heading

        reflection_prayer = ""
        try:
            reflection_prayer = element.find_element(By.CLASS_NAME, "devo-prayer").text
        except Exception as e:
            reflection_prayer = ""

        devotional_dict["reflection_prayer"] = reflection_prayer

        reflection_question = ""
        try:
            reflection_question = element.find_element(By.CLASS_NAME, "devo-question").text
        except Exception as e:
            reflection_question = ""

        devotional_dict["reflection_question"] = reflection_question

    finally:
        browser.quit()
    return devotional_dict


def get_url(day_str: str) -> str:
    return 'https://nuestropandiario.org/{day_str}'.format(day_str=day_str)
    # return 'https://odb.org/{day_str}'.format(day_str=day_str)


def get_current_devotionals(p_current_str: str) -> Tuple[List[Dict], str]:
    devotionals = []
    (current, current_str) = get_current_and_str(p_current_str)
    day = get_weekday_str(current)
    month = get_month_str(current)
    url = get_url(current_str)
    devotional_dict = scrap_webpage(url, day)
    devotionals.append(devotional_dict)
    filename = "Devoción del {day} {n} de {month}".format(day=day, n=current.day,  month=month)
    return devotionals, filename


def get_today_devotionals() -> Tuple[List[Dict], str]:
    devotionals = []
    (today, today_str) = get_today_and_str()
    day = get_weekday_str(today)
    month = get_month_str(today)
    url = get_url(today_str)
    devotional_dict = scrap_webpage(url, day)
    devotionals.append(devotional_dict)
    filename = "Devoción del {day} {n} de {month}".format(day=day, n=today.day, month=month)
    return devotionals, filename


def get_next_week_sunday_from_current(p_current_str: str):
    current : datetime.date = datetime.date.fromisoformat(p_current_str)
    next_week_sunday = current + datetime.timedelta(days=(6 - current.weekday()))
    next_week_sunday_str : str = next_week_sunday.strftime("%Y/%m/%d")
    return (next_week_sunday, next_week_sunday_str)


def get_next_week_devotionals(p_current_str: str) -> Tuple[List[Dict], str]:
    days_to_start_capture : int = 0
    days_to_end_capture : int = 6
    devotionals : List[Dict] = []
    first_day : str = ""
    first_n : str = ""
    last_day : str = ""
    last_n : str = ""
    (next_day, _) = get_next_week_sunday_from_current(p_current_str)
    for i in range(days_to_start_capture, days_to_end_capture + 1):
        (next_day, nextday_str) = get_next_day_and_str(next_day)
        day = get_weekday_str(next_day)
        first_day = day if i == days_to_start_capture else first_day
        first_n = next_day.day if i == days_to_start_capture else first_n
        last_day = day if i == days_to_end_capture else last_day
        last_n = next_day.day if i == days_to_end_capture else last_n
        month = get_month_str(next_day)
        url = get_url(nextday_str)
        try:
            devotional_dict = scrap_webpage(url, day)
            devotionals.append(devotional_dict)
        except Exception as e:
            print("Failed to get {day} at {url}".format(day=day, url=url), file=sys.stderr)
            raise e
    filename = "Devociones del {first_n} al {last_n} de {month}".format(first_n=first_n, last_n=last_n, month=month)
    return devotionals, filename


def convert_file(filename):
    full_filename = os.path.join(build_path, filename)
    html = HTML('{filename}.html'.format(filename=full_filename))
    css = CSS(string='@page { size: A4; margin: 1cm }')
    html.write_pdf('{filename}.pdf'.format(filename=full_filename), stylesheets=[css])


def write_and_convert(build_path, filename, devotionals):
    full_filename = os.path.join(build_path, filename)
    with open("{filename}.html".format(filename=full_filename), mode="w+") as file:
        file.write(template.render({'devotionals': devotionals}))
    convert_file(filename=filename)


@subcommand(
    [
        argument("-d", "--date", help="Current date. In ISO format YYYY-MM-DD", required=True)
    ]
)
def current(args):
    try:
        (devotionals, filename) = get_current_devotionals(args.date)
        write_and_convert(build_path, filename, devotionals)
    except Exception as e:
        raise e
        # print(e, file=sys.stderr)
        # sys.exit(1)


@subcommand(
    [
    ]
)
def today(args):
    try:
        (devotionals, filename) = get_today_devotionals()
        write_and_convert(build_path, filename, devotionals)
    except Exception as e:
        raise e
        # print(e, file=sys.stderr)
        # sys.exit(1)


def get_next_month_start_n_end(p_current_str: str) -> Tuple[datetime.date, datetime.date]:
    tomorrow, _ = get_current_and_str(p_current_str)
    month_start = datetime.date(tomorrow.year, tomorrow.month, 1)
    next_month = (tomorrow.month + 1)
    next_month = 1 if next_month == 13 else next_month
    carry_year = 1 if next_month == 13 else 0
    month_end = datetime.date(tomorrow.year + carry_year, next_month, 1) - datetime.timedelta(days=1)
    return (month_start, month_end)


def get_month_devotionals(p_current_str: str) -> List[List[Dict]]:
    devotionals_all = []
    devotionals = []
    (month_start, month_end) = get_next_month_start_n_end(p_current_str)
    today = month_start
    while today <= month_end:
        day = get_weekday_str(today)
        month = get_month_str(today)
        url = get_url(today.strftime("%Y/%m/%d"))
        devotional_dict = scrap_webpage(url, day)
        devotional_dict['month'] = month
        devotional_dict['dayn'] = today.day
        devotionals.append(devotional_dict)
        if day == "Domingo" or today == month_end:
            devotionals_all.append(devotionals)
            try:
                d1 = devotionals[0]
                d2 = devotionals[-1]
                filename = "Devociones del {day1} al {day2} de {month}".format(day1=d1["dayn"], day2=d2["dayn"], month=d1["month"])
                write_and_convert(build_path, filename, devotionals)
            except Exception as e:
                print("Error obtaining values from {day}")
                print(e)
            devotionals = []
        today = today + datetime.timedelta(days=1)
    return devotionals_all


@subcommand(
    [
        argument("-d", "--date", help="Current date. In ISO format YYYY-MM-DD", required=False)
    ]
)
def month(args):
    current_date_str = args.date
    if not current_date_str:
        (today, _) = get_today_and_str()
        current_date_str = today.isoformat()
    try:
        devotionals_all = get_month_devotionals(current_date_str)
    except Exception as e:
        raise e
        # print(e, file=sys.stderr)
        # sys.exit(1)


@subcommand(
    [
        argument("-d", "--date", help="Current date. In ISO format YYYY-MM-DD", required=False)
    ]
)
def next_week(args):
    current_date_str = args.date
    if not current_date_str:
        (today, _) = get_today_and_str()
        current_date_str = today.isoformat()
    try:
        (devotionals, filename) = get_next_week_devotionals(current_date_str)
        write_and_convert(build_path, filename, devotionals)
    except Exception as e:
        raise e
        # print(e, file=sys.stderr)
        # sys.exit(1)


@subcommand(
    [
        argument("-f", "--file", help="File without extension", required=True)
    ]
)
def convert(args):
    try:
        filename = args.file.replace(".html", "")
        convert_file(filename=filename)
    except Exception as e:
        raise e
        # print(e, file=sys.stderr)
        # sys.exit(1)


if __name__ == "__main__":
    makedir_helper(build_path)
    args = main_parser.parse_args()
    if args.subcommand is None:
        main_parser.print_help()
    else:
        args.func(args)

"Create a CSV file of all the jobs and their info from Washington Career Bridge"

import csv
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

RESULTS_LIMIT = 0  # only get first n jobs (set to 0 for no limiting)


def get_attribute(target_soup, label):
    """Given a target soup, find the labeled data and return it."""
    element = target_soup.find("span", id=f"ctl00_ContentPlaceHolder1_lbl{label}")
    return element.text


final_results = []

DATA_RESULTS = [
    "SubTitle",
    "NumberEmployed",
    "OpeningsPerYear",
    "MedianWages",
    "AverageWages",
    "RequiredEducationLevel",
]

for cid in tqdm(range(1, 17), desc="getting all careers"):  # 16 different cluster IDs
    cluster_page = requests.get(
        f"https://www.careerbridge.wa.gov/Detail_Cluster.aspx?jci={cid}", timeout=10
    )
    soup = BeautifulSoup(cluster_page.content, "html.parser")
    results = soup.find("div", class_="ResultsGrid")
    links = results.find_all("a")

    for link in links:
        parsed_url = urlparse(link["href"])
        soc = parse_qs(parsed_url.query)["soc"][0]

        final_results.append({"SOC": soc})

if RESULTS_LIMIT:
    final_results = final_results[:RESULTS_LIMIT]

for r in tqdm(final_results, desc="downloading career data"):

    career_page = requests.get(
        f"https://www.careerbridge.wa.gov/Detail_Occupation.aspx?soc={r['SOC']}",
        timeout=10,
    )

    career_soup = BeautifulSoup(career_page.content, "html.parser")

    title_div = career_soup.find("span", class_="site_header")

    for d in DATA_RESULTS:
        try:
            r[d] = get_attribute(career_soup, d)
        except AttributeError:
            r[d] = "None"


# header = final_results[0].keys()  # exclude education level
fieldnames = ["SOC"] + DATA_RESULTS  # SOC is retrieved in a different way

with open("job_stats.csv", mode="w", encoding="UTF-8") as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    for d in tqdm(final_results, desc="writing to file"):
        writer.writerow(d)

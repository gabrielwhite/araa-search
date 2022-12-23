from flask import Flask, request, render_template, jsonify
import requests
import random
from bs4 import BeautifulSoup
from html import escape
import time
import json

app = Flask(__name__, static_folder="static", static_url_path="")

@app.route("/suggestions")
def suggestions():
            query = request.args.get("q", "").strip()
            query = escape(query)
            response = requests.get(f"https://search.brave.com/api/suggest?q={query}")
            return json.loads(response.text)
        
@app.route("/api")
def api():
        query = request.args.get("q", "").strip()
        query = escape(query)
        try:
            response = requests.get(f"http://localhost:8000/search?q={query}&api=true")
            return json.loads(response.text)
        except Exception as e:
            app.logger.error(e)
            return jsonify({"error": "An error occurred while processing the request"}), 500

@app.route("/", methods=["GET", "POST"])
@app.route("/search", methods=["GET", "POST"])
def search():
    api = request.args.get("api", "false")
    if request.method == "GET":
        # get the `q` query parameter from the URL
        query = request.args.get("q", "").strip()
        # sanitize user input to prevent XSS
        query = escape(query)
        if query == "":
            return app.send_static_file("search.html")

        # random useragent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
        ]
        user_agent = random.choice(user_agents)
        headers = {"User-Agent": user_agent}

        # time
        start_time = time.time()

        # search query
        html = requests.get(f"https://www.google.com/search?q={query}", headers = headers)

        # object to parse html
        soup = BeautifulSoup(html.text, "lxml")

        # retrieve links
        result_divs = soup.findAll("div", {"class": "yuRUbf"})
        links = [div.find("a") for div in result_divs]
        hrefs = [link.get("href") for link in links]

        # retrieve title
        h3 = [div.find("h3") for div in result_divs]
        titles = [titles.text.strip() for titles in h3]

        # retrieve description
        result_desc = soup.findAll("div", {"class": "VwiC3b"})
        descriptions = [descs.text.strip() for descs in result_desc]

        # retrieve kno-rdesc
        try:
            rdesc = soup.find("div", {"class": "kno-rdesc"})
            span_element = rdesc.find("span")
            kno = span_element.text
            desc_link = rdesc.find("a")
            kno_link = desc_link.get("href")
        except:
            kno = ""
            kno_link = ""

        # retrieve featured snippet
        try:
            featured_snip = soup.find("span", {"class": "hgKElc"})
            snip = featured_snip.text.strip()
        except:
            snip = ""

        # list
        results = []
        for href, title, desc in zip(hrefs, titles, descriptions):
            results.append([href, title, desc])

        end_time = time.time()
        elapsed_time = end_time - start_time
        
        if api == "true":
            # return the results list as a JSON response
            return jsonify(results)
        else:
            return render_template("results.html", results = results, title = f"{query} - TailsX",
            q = f"{query}", fetched = f"Fetched the results in {elapsed_time:.2f} seconds",
            snip = f"{snip}", kno_rdesc = f"{kno}", rdesc_link = f"{kno_link}")

if __name__ == "__main__":
    # WARN: run() is not intended to be used in a production setting!
    # see https://flask.palletsprojects.com/en/2.2.x/deploying/ for more info
    app.run(threaded=True, port=5000)

from bs4 import BeautifulSoup
import requests
import smtplib
import os
import re
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

url = "https://www.ikea.com/ro/ro/p/pax-auli-dulap-usi-glisante-alb-oglinda-s59561329/"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) "
        "Gecko/20100101 Firefox/131.0"
    ),
    "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
}

def parse_price_ro(price_text: str) -> tuple[str, Decimal]:
    """
    Returnează:
      - price_display: exact cum vrei să-l arăți (ex: '4.290' sau '4.290,00')
      - price_value: valoare numerică pentru comparații (Decimal), ex: 4290 sau 4290.00
    """
    # Prinde numărul complet cu separatori RO: 1.234 sau 1.234,56
    m = re.search(r"(\d{1,3}(?:\.\d{3})*(?:,\d+)?)", price_text)
    if not m:
        raise Exception(f"Nu pot extrage prețul din: {price_text}")

    price_display = m.group(1)

    # Normalizează pentru calcule: scoate mii (.) și schimbă zecimale (, -> .)
    normalized = price_display.replace(".", "").replace(",", ".")
    price_value = Decimal(normalized)

    return price_display, price_value

resp = requests.get(url, headers=headers)
resp.raise_for_status()
soup = BeautifulSoup(resp.text, "html.parser")

# --- Title ---
title_tag = soup.select_one("h1")
title = title_tag.get_text(strip=True) if title_tag else "Unknown product"
print("TITLE:", title)

# --- Price ---
price_tag = soup.select_one(".pipcom-price__nowrap") or soup.select_one(".pipcom-price__integer")

if not price_tag:
    with open("ikea_page.html", "w", encoding="utf-8") as f:
        f.write(resp.text)
    raise Exception("Nu am găsit prețul. Am salvat pagina în ikea_page.html (structură diferită / bot-check).")

price_text = price_tag.get_text(" ", strip=True)
print("RAW PRICE:", price_text)

price_display, price_value = parse_price_ro(price_text)
print("PRICE DISPLAY:", price_display)   # ex: 4.290
print("PRICE VALUE:", price_value)       # ex: 4290

# --- Alert ---
BUY_PRICE = Decimal("1800")

if price_value < BUY_PRICE:
    message = f"{title} is on sale for {price_display} lei!"
    with smtplib.SMTP(os.environ["SMTP_ADDRESS"], port=587) as connection:
        connection.starttls()
        connection.login(os.environ["EMAIL_ADDRESS"], os.environ["EMAIL_PASSWORD"])
        connection.sendmail(
            from_addr=os.environ["EMAIL_ADDRESS"],
            to_addrs=os.environ["EMAIL_ADDRESS"],
            msg=f"Subject:Ikea Price Alert!\n\n{message}\n{url}".encode("utf-8")
        )

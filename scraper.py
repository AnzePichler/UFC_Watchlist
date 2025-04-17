import json
import requests
from bs4 import BeautifulSoup

# =======================
# Scraper Functions
# =======================

def scrape_sherdog(url):
    """
    Scrape the fighter page on Sherdog and extract:
      - profile image URL,
      - nickname,
      - division,
      - record (wins, losses, draws),
      - next_fight (event, date, location, opponent name, opponent image, opponent record)
    Returns a dictionary with these keys. Name and URL are not touched.
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

    soup = BeautifulSoup(res.text, "html.parser")

    # === Extract Main Profile Image ===
    img_tag = soup.find("img", class_="profile-image photo")
    if img_tag and img_tag.has_attr('src'):
        src = img_tag['src']
        image_url = src if src.startswith('http') else f"https://www.sherdog.com{src}"
    else:
        image_url = None

    # === Extract Fighter Bio Info ===
    bio_div = soup.find("div", class_="fighter-right")
    nickname = division = ""
    record = {"wins": 0, "losses": 0, "draws": 0}

    if bio_div:
        nn = bio_div.find("span", class_="nickname")
        nickname = nn.get_text(strip=True) if nn else ""
        assoc = bio_div.find("div", class_="association-class")
        if assoc:
            a_tags = assoc.find_all("a")
            if a_tags:
                division = a_tags[-1].get_text(strip=True)
        wl = bio_div.find("div", class_="winsloses-holder")
        if wl:
            win_div = wl.find("div", class_="winloses win")
            if win_div:
                spans = win_div.find_all("span")
                if len(spans) >= 2:
                    try:
                        record["wins"] = int(spans[1].get_text(strip=True))
                    except ValueError:
                        pass
            lose_div = wl.find("div", class_="winloses lose")
            if lose_div:
                spans = lose_div.find_all("span")
                if len(spans) >= 2:
                    try:
                        record["losses"] = int(spans[1].get_text(strip=True))
                    except ValueError:
                        pass

    # === Extract Upcoming Fight Info ===
    fight_card = soup.find("div", class_="fight_card_preview")
    next_fight = None
    if fight_card:
        # Event name
        ev = fight_card.find("h2", itemprop="name")
        event_name = ev.get_text(strip=True) if ev else ""
        # Date & Location
        dl = fight_card.find("div", class_="date_location")
        if dl:
            sd = dl.find("meta", itemprop="startDate")
            date_text = sd["content"].split("T")[0] if sd and sd.has_attr("content") else ""
            loc = dl.find("em", itemprop="location")
            location_text = " ".join(loc.stripped_strings) if loc else ""
        else:
            date_text = location_text = ""
        # Opponent info
        fight = fight_card.find("div", class_="fight")
        opponent_name = opponent_image_url = opponent_record = ""
        if fight:
            opp = fight.find("div", class_="fighter right_side")
            if opp:
                on = opp.find("span", itemprop="name")
                opponent_name = on.get_text(strip=True) if on else ""
                img = opp.find("img", itemprop="image")
                if img and img.has_attr('src'):
                    src = img['src']
                    opponent_image_url = src if src.startswith('http') else f"https://www.sherdog.com{src}"
                rec = opp.find("span", class_="record")
                opponent_record = rec.get_text(strip=True).split(" ")[0] if rec else ""
        next_fight = {
            "event": event_name,
            "date": date_text,
            "location": location_text,
            "opponent": opponent_name,
            "opponent_image_url": opponent_image_url,
            "opponent_record": opponent_record
        }

    return {
        "image_url": image_url,
        "nickname": nickname,
        "division": division,
        "record": record,
        "next_fight": next_fight
    }

# =======================
# Master Scraping Routine
# =======================

def main():
    with open("fighters.json", "r", encoding="utf-8") as f:
        fighters = json.load(f)

    scrapers = {"sherdog": scrape_sherdog}

    for fighter in fighters:
        site = fighter.get("website")
        url = fighter.get("url")
        name = fighter.get("name", "Unknown")
        if not site or not url or site not in scrapers:
            print(f"Skipping {name}: missing or unsupported source.")
            continue
        print(f"Scraping {name}...")
        info = scrapers[site](url)
        if info:
            fighter["image_url"] = info.get("image_url")
            fighter["nickname"] = info.get("nickname", fighter.get("nickname"))
            fighter["division"] = info.get("division", fighter.get("division"))
            fighter["record"] = info.get("record", fighter.get("record"))
            fighter["next_fight"] = info.get("next_fight", fighter.get("next_fight"))
            print(f"Updated {name}.")
        else:
            print(f"No data for {name}.")

    with open("fighters.json", "w", encoding="utf-8") as f:
        json.dump(fighters, f, ensure_ascii=False, indent=2)
    print("All done.")

if __name__ == "__main__":
    main()

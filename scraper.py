import json
import requests
from bs4 import BeautifulSoup


# =======================
# Scraper Functions
# =======================

def scrape_sherdog(url):
    """
    Scrape the fighter page on Sherdog and extract:
      - nickname,
      - division,
      - record (wins, losses, draws),
      - next_fight (event, date, location, opponent)
    Returns a dictionary with these keys. Name and URL are not touched.
    """
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            print(f"Error fetching {url}: status code {res.status_code}")
            return None
    except Exception as e:
        print(f"Request failed for {url}: {e}")
        return None

    soup = BeautifulSoup(res.text, "html.parser")

    # === Extract Fighter Bio Info ===
    # Locate the bio container – typically the "fighter-right" div.
    bio_div = soup.find("div", class_="fighter-right")

    if bio_div:
        # Extract nickname from an element with class "nickname".
        nickname_tag = bio_div.find("span", class_="nickname")
        nickname = nickname_tag.get_text(strip=True) if nickname_tag else ""

        # Extract division:
        # In the bio, there's a div "association-class" which lists association and then CLASS.
        assoc_div = bio_div.find("div", class_="association-class")
        if assoc_div:
            # We assume that the last <a> element within it has the weightclass (division).
            a_tags = assoc_div.find_all("a")
            if a_tags:
                division = a_tags[-1].get_text(strip=True)
            else:
                division = ""
        else:
            division = ""

        # Extract record from the "winsloses-holder" block.
        record = {"wins": 0, "losses": 0, "draws": 0}
        winsloses_holder = bio_div.find("div", class_="winsloses-holder")
        if winsloses_holder:
            # Extract wins
            wins_div = winsloses_holder.find("div", class_="wins")
            if wins_div:
                win_box = wins_div.find("div", class_="winloses win")
                if win_box:
                    spans = win_box.find_all("span")
                    if len(spans) >= 2:
                        try:
                            record["wins"] = int(spans[1].get_text(strip=True))
                        except ValueError:
                            record["wins"] = 0
            # Extract losses
            loses_div = winsloses_holder.find("div", class_="loses")
            if loses_div:
                lose_box = loses_div.find("div", class_="winloses lose")
                if lose_box:
                    spans = lose_box.find_all("span")
                    if len(spans) >= 2:
                        try:
                            record["losses"] = int(spans[1].get_text(strip=True))
                        except ValueError:
                            record["losses"] = 0
            # Draws may not be present; default to 0.
    else:
        nickname = ""
        division = ""
        record = {"wins": 0, "losses": 0, "draws": 0}

    # === Extract Upcoming Fight Info ===
    fight_card = soup.find("div", class_="fight_card_preview")
    if fight_card:
        # Extract Event Name (e.g., from <h2 itemprop="name">UFC on ESPN 66</h2>)
        event_name_tag = fight_card.find("h2", itemprop="name")
        event_name = event_name_tag.get_text(strip=True) if event_name_tag else "N/A"

        # Extract Date and Location from the "date_location" div.
        date_location_div = fight_card.find("div", class_="date_location")
        if date_location_div:
            start_date_meta = date_location_div.find("meta", itemprop="startDate")
            date_text = (start_date_meta["content"].split("T")[0]
                         if start_date_meta and start_date_meta.has_attr("content")
                         else "N/A")
            location_em = date_location_div.find("em", itemprop="location")
            location_text = " ".join(location_em.stripped_strings) if location_em else "N/A"
        else:
            date_text = "N/A"
            location_text = "N/A"

        # Extract Opponent's Name: search in the fight block for the right-side fighter.
        fight_div = fight_card.find("div", class_="fight")
        if fight_div:
            fighter_right = fight_div.find("div", class_="fighter right_side")
            if fighter_right:
                opponent_name_tag = fighter_right.find("span", itemprop="name")
                opponent_name = opponent_name_tag.get_text(strip=True) if opponent_name_tag else "N/A"
            else:
                opponent_name = "N/A"
        else:
            opponent_name = "N/A"

        next_fight = {
            "event": event_name,
            "date": date_text,
            "location": location_text,
            "opponent": opponent_name
        }
    else:
        next_fight = None

    return {
        "nickname": nickname,
        "division": division,
        "record": record,
        "next_fight": next_fight
    }


# If needed, additional scraper functions for other websites can be added here.

# =======================
# Master Scraping Routine
# =======================

def main():
    # Load existing fighter data from fighters.json
    with open("fighters.json", "r", encoding="utf-8") as f:
        fighters = json.load(f)

    # Map website identifiers to their respective scraper functions.
    scrapers = {
        "sherdog": scrape_sherdog
        # Add other mappings for different sites if needed.
    }

    for fighter in fighters:
        website = fighter.get("website")
        url = fighter.get("url")
        name = fighter.get("name", "Unknown Fighter")

        if not url or not website:
            print(f"Skipping {name}: missing URL or website data.")
            continue
        if website not in scrapers:
            print(f"Skipping {name}: no scraper available for website '{website}'.")
            continue

        print(f"Scraping info for {name} from {website}...")
        scraper_func = scrapers[website]
        scraped_info = scraper_func(url)
        if scraped_info:
            # Update fighter entry while preserving "name" and "url".
            fighter["nickname"] = scraped_info.get("nickname", fighter.get("nickname", ""))
            fighter["division"] = scraped_info.get("division", fighter.get("division", ""))
            fighter["record"] = scraped_info.get("record", fighter.get("record", {"wins": 0, "losses": 0, "draws": 0}))
            fighter["next_fight"] = scraped_info.get("next_fight", fighter.get("next_fight"))
            print(f"Updated info for {name}.")
        else:
            print(f"No updated info found for {name}. Keeping existing data.")

    # Overwrite the existing fighters.json file with the updated data.
    with open("fighters.json", "w", encoding="utf-8") as f:
        json.dump(fighters, f, ensure_ascii=False, indent=2)

    print("Scraping complete. fighters.json has been updated.")


if __name__ == "__main__":
    main()

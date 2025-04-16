from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a secure key

FIGHTERS_JSON = 'fighters.json'


def load_fighters():
    """Load fighter data from the JSON file."""
    if os.path.exists(FIGHTERS_JSON):
        with open(FIGHTERS_JSON, 'r', encoding='utf-8') as f:
            fighters = json.load(f)
    else:
        fighters = []
    return fighters


def save_fighters(fighters):
    """Save fighter data back to the JSON file."""
    with open(FIGHTERS_JSON, 'w', encoding='utf-8') as f:
        json.dump(fighters, f, ensure_ascii=False, indent=2)


@app.route('/')
def index():
    """Main page displaying the fighters watchlist."""
    fighters = load_fighters()
    return render_template('index.html', fighters=fighters)


@app.route('/add', methods=['GET', 'POST'])
def add_fighter():
    """Route for adding a new fighter to the watchlist."""
    if request.method == 'POST':
        # Extract data from the submitted form
        name = request.form.get('name')
        nickname = request.form.get('nickname')
        division = request.form.get('division')
        website = request.form.get('website')
        url = request.form.get('url')
        try:
            wins = int(request.form.get('wins', 0))
            losses = int(request.form.get('losses', 0))
            draws = int(request.form.get('draws', 0))
        except ValueError:
            wins = losses = draws = 0

        new_fighter = {
            "name": name,
            "nickname": nickname,
            "division": division,
            "record": {
                "wins": wins,
                "losses": losses,
                "draws": draws
            },
            "website": website,
            "url": url,
            "next_fight": None
        }

        fighters = load_fighters()
        fighters.append(new_fighter)
        save_fighters(fighters)
        flash("Fighter added successfully!")
        return redirect(url_for('index'))
    return render_template('add_fighter.html')


@app.route('/delete/<int:index>', methods=['POST'])
def delete_fighter(index):
    """Route to delete a fighter by index in the JSON file."""
    fighters = load_fighters()
    if index < len(fighters):
        deleted = fighters.pop(index)
        save_fighters(fighters)
        flash(f"Fighter {deleted.get('name')} removed.")
    else:
        flash("Invalid fighter index!")
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)

"""
Build script: reads recipes/*.json and generates a static site in docs/.
Run: python build.py
"""
import json
import os
import glob
from pathlib import Path

ROOT = Path(__file__).parent
RECIPES_DIR = ROOT / "recipes"
DOCS_DIR = ROOT / "docs"
TEMPLATE_PATH = ROOT / "template.html"


def load_recipes():
    recipes = []
    for path in sorted(RECIPES_DIR.glob("*.json")):
        with open(path, "r", encoding="utf-8") as f:
            recipe = json.load(f)
            recipe["_slug"] = path.stem
            recipes.append(recipe)
    return recipes


def build_recipe_card(r):
    ingredients_html = "".join(f"<li>{i}</li>" for i in r["recipe"]["ingredients"])
    steps_html = "".join(f"<li>{s}</li>" for s in r["recipe"]["steps"])

    notes_html = ""
    if r.get("notes"):
        notes_html = f'<div class="notes"><strong>Notes:</strong> {r["notes"]}</div>'

    serving_html = ""
    if r["recipe"].get("serving"):
        serving_html = f'<div class="serving"><strong>Serving:</strong> {r["recipe"]["serving"]}</div>'

    storage_html = ""
    if r["recipe"].get("storage"):
        storage_html = f'<div class="storage"><strong>Storage:</strong> {r["recipe"]["storage"]}</div>'

    source_html = ""
    if r.get("source"):
        source_html = f'<div class="source">{r["source"]}</div>'

    yield_html = ""
    if r["recipe"].get("yield"):
        yield_html = f'<span class="yield">{r["recipe"]["yield"]}</span>'

    return f"""
    <article class="recipe-card" id="{r['_slug']}">
      <div class="recipe-header" onclick="toggleRecipe(this)">
        <h2>{r['dish']}</h2>
        <div class="recipe-meta">
          {yield_html}
          {source_html}
        </div>
        <span class="toggle-icon">+</span>
      </div>
      <div class="recipe-body">
        <h3>Ingredients</h3>
        <ul class="ingredients">{ingredients_html}</ul>
        <h3>Steps</h3>
        <ol class="steps">{steps_html}</ol>
        {notes_html}
        {serving_html}
        {storage_html}
      </div>
    </article>
    """


def build_site():
    recipes = load_recipes()
    cards_html = "\n".join(build_recipe_card(r) for r in recipes)

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    html = template.replace("{{RECIPE_CARDS}}", cards_html)
    html = html.replace("{{RECIPE_COUNT}}", str(len(recipes)))

    DOCS_DIR.mkdir(exist_ok=True)
    with open(DOCS_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Built {len(recipes)} recipes -> docs/index.html")


if __name__ == "__main__":
    build_site()

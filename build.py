"""
Build script: reads recipes/*.json and generates a static site in docs/.
Run: python build.py
"""
import json
from html import escape
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


def collect_tags(recipes):
    meal_tags = set()
    cuisine_tags = set()
    for r in recipes:
        tags = r.get("tags", {})
        meal_tags.update(tags.get("meal", []))
        cuisine_tags.update(tags.get("cuisine", []))
    return sorted(meal_tags), sorted(cuisine_tags)


def build_recipe_card(r):
    ingredients_html = "".join(
        f'<li data-original="{escape(i)}">{escape(i)}</li>'
        for i in r["recipe"]["ingredients"]
    )
    steps_html = "".join(f"<li>{escape(s)}</li>" for s in r["recipe"]["steps"])

    tags = r.get("tags", {})
    all_tags = tags.get("meal", []) + tags.get("cuisine", [])
    data_tags = " ".join(all_tags)

    tag_pills = "".join(f'<span class="tag-pill">{escape(t)}</span>' for t in all_tags)

    notes_html = ""
    if r.get("notes"):
        notes_html = f'<div class="notes"><strong>Notes:</strong> {escape(r["notes"])}</div>'

    serving_html = ""
    if r["recipe"].get("serving"):
        serving_html = f'<div class="serving"><strong>Serving:</strong> {escape(r["recipe"]["serving"])}</div>'

    storage_html = ""
    if r["recipe"].get("storage"):
        storage_html = f'<div class="storage"><strong>Storage:</strong> {escape(r["recipe"]["storage"])}</div>'

    source_html = ""
    if r.get("source"):
        source_html = f'<div class="source">{escape(r["source"])}</div>'

    yield_html = ""
    if r["recipe"].get("yield"):
        yield_html = f'<span class="yield">{escape(r["recipe"]["yield"])}</span>'

    return f"""
    <article class="recipe-card" id="{escape(r['_slug'])}" data-tags="{escape(data_tags)}">
      <div class="recipe-header" onclick="toggleRecipe(this)">
        <h2>{escape(r['dish'])}</h2>
        <div class="recipe-meta">
          {yield_html}
          {source_html}
          <div class="tag-pills">{tag_pills}</div>
        </div>
        <span class="toggle-icon">+</span>
      </div>
      <div class="recipe-body">
        <h3>Ingredients</h3>
        <div class="scaler">
          <button class="scale-btn" onclick="scaleRecipe(this, 0.5)">&#189;x</button>
          <button class="scale-btn active" onclick="scaleRecipe(this, 1)">1x</button>
          <button class="scale-btn" onclick="scaleRecipe(this, 2)">2x</button>
          <button class="scale-btn" onclick="scaleRecipe(this, 3)">3x</button>
        </div>
        <ul class="ingredients">{ingredients_html}</ul>
        <h3>Steps</h3>
        <ol class="steps">{steps_html}</ol>
        {notes_html}
        {serving_html}
        {storage_html}
      </div>
    </article>
    """


def build_recipe_summary(recipes):
    """Build a text summary of all recipes for the chef chat context."""
    lines = []
    for r in recipes:
        tags = r.get("tags", {})
        tag_str = ", ".join(tags.get("meal", []) + tags.get("cuisine", []))
        notes = f" Notes: {r['notes']}" if r.get("notes") else ""
        ingredients = ", ".join(r["recipe"]["ingredients"])
        lines.append(
            f"- {r['dish']} ({tag_str}): {r['recipe'].get('yield', 'No yield listed')}. "
            f"Ingredients: {ingredients}.{notes}"
        )
    return "\\n".join(lines)


def build_site():
    recipes = load_recipes()
    meal_tags, cuisine_tags = collect_tags(recipes)
    cards_html = "\n".join(build_recipe_card(r) for r in recipes)
    recipe_summary = build_recipe_summary(recipes)

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    # Build tag filter buttons
    meal_btns = "".join(f'<button class="filter-btn" data-tag="{escape(t)}">{escape(t)}</button>' for t in meal_tags)
    cuisine_btns = "".join(f'<button class="filter-btn" data-tag="{escape(t)}">{escape(t)}</button>' for t in cuisine_tags)

    # Build tag checkboxes for the add form
    meal_checks = "".join(
        f'<label class="check-label"><input type="checkbox" value="{escape(t)}"> {escape(t)}</label>'
        for t in meal_tags
    )
    cuisine_checks = "".join(
        f'<label class="check-label"><input type="checkbox" value="{escape(t)}"> {escape(t)}</label>'
        for t in cuisine_tags
    )

    html = template.replace("{{RECIPE_CARDS}}", cards_html)
    html = html.replace("{{RECIPE_COUNT}}", str(len(recipes)))
    html = html.replace("{{MEAL_TAG_BUTTONS}}", meal_btns)
    html = html.replace("{{CUISINE_TAG_BUTTONS}}", cuisine_btns)
    html = html.replace("{{MEAL_TAG_CHECKS}}", meal_checks)
    html = html.replace("{{CUISINE_TAG_CHECKS}}", cuisine_checks)
    html = html.replace("{{RECIPE_SUMMARY}}", recipe_summary)

    DOCS_DIR.mkdir(exist_ok=True)
    with open(DOCS_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Built {len(recipes)} recipes -> docs/index.html")


if __name__ == "__main__":
    build_site()

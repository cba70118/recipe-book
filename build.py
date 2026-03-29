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

TAG_CATEGORIES = ["who", "meal", "cuisine", "protein", "style", "occasion", "tool"]


def load_recipes():
    recipes = []
    for path in sorted(RECIPES_DIR.glob("*.json")):
        with open(path, "r", encoding="utf-8") as f:
            recipe = json.load(f)
            recipe["_slug"] = path.stem
            recipes.append(recipe)
    return recipes


def collect_all_tags(recipes):
    """Collect tags across all categories."""
    tag_sets = {cat: set() for cat in TAG_CATEGORIES}
    for r in recipes:
        tags = r.get("tags", {})
        for cat in TAG_CATEGORIES:
            tag_sets[cat].update(tags.get(cat, []))
    return {cat: sorted(vals) for cat, vals in tag_sets.items()}


def build_recipe_card(r, all_recipes=None):
    ingredients_html = "".join(
        f'<li data-original="{escape(i)}">{escape(i)}</li>'
        for i in r["recipe"]["ingredients"]
    )
    steps_html = "".join(f"<li>{escape(s)}</li>" for s in r["recipe"]["steps"])

    # Collect ALL tags for data attribute (used for filtering)
    tags = r.get("tags", {})
    all_tags = []
    for cat in TAG_CATEGORIES:
        all_tags.extend(tags.get(cat, []))
    data_tags = " ".join(all_tags)

    tag_pills = "".join(f'<span class="tag-pill">{escape(t)}</span>' for t in all_tags)

    # Why This Works + You Might Also Like
    also_like = r.get("you_might_also_like", [])
    similar_html = ""
    if also_like:
        links = "".join(
            f'<a href="{escape(item["url"])}" target="_blank" rel="noopener" class="similar-link">{escape(item["dish"])}</a>'
            for item in also_like
        )
        similar_html = f'<div class="similar-recipes"><strong>You Might Also Like:</strong> {links}</div>'

    why_html = ""
    if r.get("why_this_works"):
        why_html = f'<div class="why-this-works"><strong>Why This Works:</strong> {escape(r["why_this_works"])}{similar_html}</div>'
    elif similar_html:
        why_html = similar_html

    # Difficulty + Time
    meta_bits = []
    if r.get("difficulty"):
        meta_bits.append(escape(r["difficulty"]))
    if r.get("time", {}).get("total"):
        meta_bits.append(escape(r["time"]["total"]))
    difficulty_time = f'<span class="difficulty-time">{" · ".join(meta_bits)}</span>' if meta_bits else ""

    notes_html = ""
    if r.get("notes"):
        notes_html = f'<div class="notes"><strong>Notes:</strong> {escape(r["notes"])}</div>'

    serving_html = ""
    if r["recipe"].get("serving"):
        serving_html = f'<div class="serving"><strong>Serving:</strong> {escape(r["recipe"]["serving"])}</div>'

    storage_html = ""
    if r["recipe"].get("storage"):
        storage_html = f'<div class="storage"><strong>Storage:</strong> {escape(r["recipe"]["storage"])}</div>'

    family_notes_html = ""
    if r.get("family_notes"):
        family_notes_html = f'<div class="family-notes"><strong>Family Notes:</strong> {escape(r["family_notes"])}</div>'

    source_html = ""
    if r.get("source"):
        source_html = f'<div class="source">{escape(r["source"])}</div>'

    yield_html = ""
    if r["recipe"].get("yield"):
        yield_html = f'<span class="yield">{escape(r["recipe"]["yield"])}</span>'

    # Embed recipe JSON for edit functionality (strip internal _slug)
    recipe_json = json.dumps({k: v for k, v in r.items() if k != '_slug'})
    recipe_json_escaped = escape(recipe_json)

    return f"""
    <article class="recipe-card" id="{escape(r['_slug'])}" data-tags="{escape(data_tags)}" data-slug="{escape(r['_slug'])}" data-recipe="{recipe_json_escaped}">
      <div class="recipe-header" onclick="toggleRecipe(this)">
        <h2>{escape(r['dish'])}</h2>
        <div class="recipe-meta">
          {difficulty_time}
          {yield_html}
          {source_html}
          <div class="tag-pills">{tag_pills}</div>
        </div>
        <span class="toggle-icon">+</span>
      </div>
      <div class="recipe-body">
        {why_html}
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
        {family_notes_html}
        <div class="recipe-actions">
          <button class="recipe-action-btn edit-btn" onclick="editRecipe('{escape(r['_slug'])}')">Edit</button>
          <button class="recipe-action-btn delete-btn" onclick="deleteRecipe('{escape(r['_slug'])}', '{escape(r['dish'])}')">Delete</button>
        </div>
      </div>
    </article>
    """


def build_recipe_summary(recipes):
    """Build a text summary of all recipes for the chef chat context."""
    lines = []
    for r in recipes:
        tags = r.get("tags", {})
        tag_parts = []
        for cat in TAG_CATEGORIES:
            tag_parts.extend(tags.get(cat, []))
        tag_str = ", ".join(tag_parts)
        notes = f" Notes: {r['notes']}" if r.get("notes") else ""
        why = f" Why it works: {r['why_this_works']}" if r.get("why_this_works") else ""
        ingredients = ", ".join(r["recipe"]["ingredients"])
        difficulty = r.get("difficulty", "")
        time_total = r.get("time", {}).get("total", "")
        lines.append(
            f"- {r['dish']} [{difficulty}, {time_total}] ({tag_str}): "
            f"{r['recipe'].get('yield', 'No yield listed')}. "
            f"Ingredients: {ingredients}.{why}{notes}"
        )
    return "\\n".join(lines)


def build_site():
    recipes = load_recipes()
    all_tags = collect_all_tags(recipes)
    cards_html = "\n".join(build_recipe_card(r) for r in recipes)
    recipe_summary = build_recipe_summary(recipes)

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    # Build tag filter buttons for each category
    tag_btns = {}
    tag_checks = {}
    for cat in TAG_CATEGORIES:
        tag_btns[cat] = "".join(
            f'<button class="filter-btn" data-tag="{escape(t)}">{escape(t)}</button>'
            for t in all_tags[cat]
        )
        tag_checks[cat] = "".join(
            f'<label class="check-label"><input type="checkbox" value="{escape(t)}"> {escape(t)}</label>'
            for t in all_tags[cat]
        )

    html = template.replace("{{RECIPE_CARDS}}", cards_html)
    html = html.replace("{{RECIPE_COUNT}}", str(len(recipes)))
    html = html.replace("{{RECIPE_SUMMARY}}", recipe_summary)

    # Replace tag placeholders for each category
    for cat in TAG_CATEGORIES:
        html = html.replace(f"{{{{{cat.upper()}_TAG_BUTTONS}}}}", tag_btns[cat])
        html = html.replace(f"{{{{{cat.upper()}_TAG_CHECKS}}}}", tag_checks[cat])

    DOCS_DIR.mkdir(exist_ok=True)
    with open(DOCS_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Built {len(recipes)} recipes -> docs/index.html")


if __name__ == "__main__":
    build_site()

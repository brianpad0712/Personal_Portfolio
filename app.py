# Don't touch this file, unless error occurs

import json
import shutil
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

# Doing this to keep every path in one place
# Allowing for no hardcodes string to be scattered through the file
ROOT = Path(__file__).parent # the folder app.py is in
DATA_DIR = ROOT / "data" # where profile.json and projects.json are in
TEMPLATES_DIR = ROOT / "templates" # where the .html templates are in
STATIC_DIR = ROOT / "static" # where CSS and images are in
OUTPUT_DIR = ROOT / "docs" # where the website is eventually put


def load_data():
    # Read the two JSON files that hold all editable content.
    profile = json.loads((DATA_DIR / "profile.json").read_text())
    projects = json.loads((DATA_DIR / "projects.json").read_text())
    return profile, projects


def enrich_projects(projects):
    #Sorts newest-first so the newer projects always show up on top.
    for p in projects:
        p["_date"] = datetime.strptime(p["date"], "%Y-%m")
        p["year"] = p["_date"].year
        p["month_name"] = p["_date"].strftime("%B")

    projects.sort(key=lambda p: p["_date"], reverse=True)
    return projects


def group_by_year(projects):
    # Turns a flat list of projects into groups like:
    # [{year: 2026, entries: []}]
    # so the homepage can print one year heading, then list projects under it
    years = []
    current_year = None
    for p in projects:
        if p["year"] != current_year:
            current_year = p["year"]
            years.append({"year": current_year, "entries": []})
        years[-1]["entries"].append(p)
    return years


def build():
    # Load and prep the data
    profile, projects = load_data()
    projects = enrich_projects(projects)
    years = group_by_year(projects)

    # sey up Jina2 so it knows where to find the templates
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)

    # Delete the old docs/ folder and make a new empty one
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)
    (OUTPUT_DIR / "projects").mkdir()

    # Copy zcss and images folder into docs/ 
    shutil.copytree(STATIC_DIR, OUTPUT_DIR / "static")

    
    index_template = env.get_template("index.html")
    (OUTPUT_DIR / "index.html").write_text(
        index_template.render(
            profile=profile,
            years=years,
            project_count=len(projects),
            root="",                      # homepage links are relative to itself
        )
    )

    # one detail page per project
    project_template = env.get_template("project.html")
    for p in projects:
        page = project_template.render(
            profile=profile,
            project=p,
            project_count=len(projects),
            root="../",                   # one level up, back to the site root
        )
        (OUTPUT_DIR / "projects" / f"{p['slug']}.html").write_text(page)

    print(f"Built {len(projects)} project(s) into {OUTPUT_DIR}/")
    print(f"Open {OUTPUT_DIR / 'index.html'} in a browser to preview.")


if __name__ == "__main__":
    build()
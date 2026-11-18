"""Take a Neo4j Browser screenshot of the graph a Cypher query returns.

Usage: python screenshot.py QUERY_FILE OUTPUT_PNG NODE_SIZE

NODE_SIZE is one of Neo4j Browser's node sizes in px, for example 36.
"""

import sys

from playwright.sync_api import sync_playwright

URL = ("http://localhost:7495/browser/?dbms=neo4j://localhost:7697"
       "&preselectAuthMethod=NO_AUTH")
COLORS = {
    "biolink:Agent": "#D9C8AE",
    "biolink:DatasetVersion": "#C990C0",
    "biolink:Dataset": "#FFC454",
    "biolink:DatasetDistribution": "#8DCC93",
    "biolink:Case": "#F16667",
    "biolink:Disease": "#F79767",
    "biolink:PhenotypicFeature": "#ECB5C9",
    "biolink:Gene": "#57C7E3",
    "biolink:SmallMolecule": "#FFE081",
    "biolink:Pathway": "#569480",
}

EXTERNAL_TYPES = ["biolink:regulates", "biolink:affects",
                  "biolink:in_clinical_trials_for",
                  "biolink:actively_involved_in"]
EXTERNAL_COLOR = "#FFC454"

query, out, size = open(sys.argv[1]).read().strip(), sys.argv[2], sys.argv[3]
with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome")
    page = browser.new_page(viewport={"width": 1700, "height": 1100},
                            device_scale_factor=2)
    page.goto(URL)
    page.wait_for_timeout(4000)
    ## Authentication is disabled, so any password is accepted
    modal = page.locator(".ndl-modal-root")
    modal.locator("input[type=password]").fill("none")
    modal.get_by_role("button", name="Connect").click()
    page.wait_for_timeout(4000)
    page.get_by_role("button", name="Dismiss").click()
    for _ in range(2):
        page.get_by_role("button", name="Remove frame").first.click()
    page.locator(".cm-content").first.click()
    page.keyboard.insert_text(query)
    page.keyboard.press("Escape")
    page.get_by_test_id("run-button").click()
    page.wait_for_timeout(4000)
    for label, color in COLORS.items():
        chip = page.locator(f"button[title='{label}']")
        if not chip.count():
            continue
        chip.first.click()
        page.get_by_label(f"select-color-{color}").click()
        page.get_by_label(f"select-size-{size}px").click()
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
    ## Color the edge types from external knowledge bases
    for rel_type in EXTERNAL_TYPES:
        chip = page.locator(f"button[title='{rel_type}']")
        if not chip.count():
            continue
        chip.first.click()
        page.wait_for_timeout(300)
        page.get_by_label(f"select-color-{EXTERNAL_COLOR}").click()
        page.locator("[aria-label^='select-width']").nth(2).click()
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
    page.get_by_role("button", name="Toggle graph details panel").click()
    ## The button before the frame's Run button makes the frame fullscreen
    page.get_by_role("button", name="Run").nth(1).locator(
        "xpath=preceding-sibling::button[1]").click()
    page.wait_for_timeout(1500)
    page.get_by_role("button", name="Zoom to fit").click()
    page.get_by_role("button", name="Zoom in").click()
    page.mouse.move(0, 0)
    page.wait_for_timeout(3000)
    graph = page.locator("canvas").first.locator("xpath=..")
    graph.screenshot(path=out)
    browser.close()

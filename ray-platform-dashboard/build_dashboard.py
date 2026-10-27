#!/usr/bin/env python3
"""
Comprehensive Dashboard Builder for Ray AI Platform & Serverless Alternative.
Outputs an executive-grade, deeply technical interactive documentation portal.
"""

import os
import shutil

OUTPUT_DIR = "/Users/jashkv/Desktop/assignment-1/ray-platform-dashboard"
OUTPUT_HTML = os.path.join(OUTPUT_DIR, "index.html")
ROOT_HTML = "/Users/jashkv/Desktop/assignment-1/index.html"

def generate_html():
    # We construct the HTML in parts to maintain absolute clarity and prevent truncation
    from sections import get_head, get_nav, get_hero, get_app_section, get_config_section, \
        get_setup_section, get_tf_section, get_order_section, get_pipeline_section, \
        get_cost_section, get_serverless_section, get_security_section, get_tools_section, \
        get_footer, get_scripts

    html = []
    html.append("<!DOCTYPE html>\n<html lang=\"en\" data-theme=\"dark\">\n")
    html.append(get_head())
    html.append("<body>\n")
    html.append(get_nav())
    html.append("<main>\n")
    html.append(get_hero())
    html.append(get_app_section())
    html.append(get_config_section())
    html.append(get_setup_section())
    html.append(get_tf_section())
    html.append(get_order_section())
    html.append(get_pipeline_section())
    html.append(get_cost_section())
    html.append(get_serverless_section())
    html.append(get_security_section())
    html.append(get_tools_section())
    html.append("</main>\n")
    html.append(get_footer())
    html.append(get_scripts())
    html.append("</body>\n</html>\n")

    full_html = "".join(html)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(full_html)

    shutil.copyfile(OUTPUT_HTML, ROOT_HTML)
    print(f"Successfully generated {OUTPUT_HTML} and copied to {ROOT_HTML}")
    print(f"File size: {len(full_html)} bytes, lines: {full_html.count(chr(10))}")

if __name__ == "__main__":
    generate_html()

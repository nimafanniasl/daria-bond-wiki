import requests
import base64
import json
from bs4 import BeautifulSoup

all_server_updates = []

def get_updates(codename: str, release_code: str):
    """Recursively fetch OTA updates from the server for a given codename and release code."""
    url = f"https://api.dariaos.com/ota/api/v1/{codename}/RELEASE/{release_code}/SOMETHING"
    base_response = requests.get(url).json()

    if not base_response.get("response"):
        return

    response = base_response["response"][0]
    print(f"[{codename}] Found incremental: {response['incremental']}")

    # Decode changelog from base64
    response["changes"] = base64.b64decode(response["changes"]).decode("utf-8")
    response["device"] = codename

    all_server_updates.append(response)

    # Recursively get previous updates
    get_updates(codename, response["incremental"])


def build_server_updates_html(updates):
    """Generate HTML for server-hosted OTA updates."""
    html_blocks = []
    for update in updates:
        size_gb = update["size"] / (1024 ** 3)
        html_blocks.append(f"""
        <details>
            <summary>DariaOS {update["version"]} - {update["incremental"]}</summary>
            <h3>Download: <a href="{update["url"]}">{update["filename"]}</a></h3>
            <p>
                File Size: {size_gb:.2f} GB — md5sum: {update["md5sum"]} —
                API Level: {update["api_level"]} — Channel: {update["channel"]} — Type: {update["updatetype"]}
            </p>
            <h3>Changelog:</h3>
            {update["changes"]}
        </details>
        """)
    return "\n".join(html_blocks)


def build_unlisted_updates_html(unlisted_updates, codename):
    """Generate HTML for unlisted (manual) OTA updates filtered by codename."""
    html_blocks = []
    for update in unlisted_updates:
        if update.get("device") != codename:
            continue
        size_gb = update["size"] / (1024 ** 3)
        html_blocks.append(f"""
        <details {"open" if update.get("expanded", False) else ""}>
            <summary>{update["version"]}</summary>
            <h2>توضیحات:</h2>
            {update["description"]}
            <h3>Download: <a href="{update["url"]}">{update["filename"]}</a></h3>
            {f'<h3>Download Boot + Recovery Image: <a href="{update["boot_img"]}">boot.img</a></h3>' if update.get("boot_img") else ""}
            <p>
                File Size: {size_gb:.2f} GB — md5sum: {update["md5sum"]} —
                API Level: {update["api_level"]} — Type: {update.get("updatetype", "N/A")}
            </p>
        </details>
        """)
    return "\n".join(html_blocks)


def main():
    devices = {
        "zahedan": {"name": "Daria Bond I", "release": "V0.00.0.0.BOND"},
        "hormoz": {"name": "Daria Bond II", "release": "V0.00.0.0.BOND2"},
        "qoqnoos": {"name": "Daria Bond II Lite", "release": "V0.00.0.0.BOND2L"}
    }

    with open("scripts/unlisted_updates.json", "r") as f:
        unlisted_updates = json.load(f).get("unlisted_updates", [])

    final_html = "# بارگیری رام رسمی\n\n"

    for codename, info in devices.items():
        print(f"\n=== Fetching updates for {info['name']} ({codename}) ===")
        get_updates(codename, info["release"])

        device_updates = [u for u in all_server_updates if u["device"] == codename]
        server_updates_html = build_server_updates_html(device_updates)
        unlisted_updates_html = build_unlisted_updates_html(unlisted_updates, codename)

        final_html += f"\n## {info['name']} ({codename})\n"
        if unlisted_updates_html:
            final_html += "\n### رام‌های رسمی (حذف شده از سرور داریا)\n"
            final_html += unlisted_updates_html
        final_html += "\n\n### رام‌های رسمی (سرور داریا)\n"
        final_html += server_updates_html or "_هیچ رام رسمی در سرور یافت نشد._"

    # Beautify with BeautifulSoup
    final_html = BeautifulSoup(final_html, "html.parser").prettify()

    with open("docs/official-rom.md", "w", encoding="utf-8") as f:
        f.write(final_html)
    print("\nDone! Output saved to docs/official-rom.md")


if __name__ == "__main__":
    main()
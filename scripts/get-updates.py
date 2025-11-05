import requests
import base64
from bs4 import BeautifulSoup
import json

all_server_updates = []

def get_updates(codename: str, release_code: str):
    base_response = requests.get(
        f"https://api.dariaos.com/ota/api/v1/{codename}/RELEASE/{release_code}/SOMETHING").json()
    
    if len(base_response["response"]) == 0:
        return

    response = base_response["response"][0]
    print(f"found {response['incremental']}")

    response["changes"] = base64.b64decode(response["changes"])
        
    all_server_updates.append(response)

    get_updates(codename, response["incremental"])

# Get DariaOS 4 -> 5 Updates
os4_updates = get_updates("zahedan", "V4.81.1.0.BOND")

server_updates_html = []
unlisted_updates_html = []

for update in all_server_updates:
    size_gb = update["size"] / (1024 ** 3)
    server_updates_html.append(f"""
                        <details>
                        <summary>DariaOS {update["version"]} - {update["incremental"]}</summary>

                        <h3>Download: <a href="{update["url"]}">{update["filename"]}</a></h3>
                        
                        <p>File Size: {size_gb:.2f} GB - md5sum: {update["md5sum"]} - API Level {update["api_level"]} - Channel: {update["channel"]} - Type: {update["updatetype"]}</p>

                        <h3>Changelog:</h3>
                        {update["changes"].decode("utf-8")}
                        </details>
                        """)

with open("scripts/unlisted_updates.json", "r") as f:
    unlisted_updates_info = json.load(f)["unlisted_updates"]
    for update in unlisted_updates_info:
        size_gb = update["size"] / (1024 ** 3)
        unlisted_updates_html.append(f"""
                            <details>
                            <summary>{update["version"]}</summary>

                            <h2>توضیحات:</h2>
                            {update["description"]}

                            <h3>بارگیری: <a href="{update["url"]}">{update["filename"]}</a></h3>
                            
                            <p>File Size: {size_gb:.2f} GB - md5sum: {update["md5sum"]} - API Level {update["api_level"]} - Type: {update.get("updatetype", "N/A")}</p>
                            </details>
                            """)
    

final_html = """
# بارگیری رام رسمی
"""

final_html += "# رام های رسمی (حذف شده از سرور داریا)"

unlisted_updates_html = "\n".join(unlisted_updates_html)

final_html += unlisted_updates_html

final_html += "# رام های رسمی (سرور داریا)"

server_updates_html = "\n".join(server_updates_html)

final_html += server_updates_html

soup = BeautifulSoup(final_html, "html.parser")
final_html = soup.prettify()

with open("docs/official-rom.md", "w") as f:
    f.write(final_html)
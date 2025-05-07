import argparse
import json
import re
from itertools import chain
from pathlib import Path

import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", help="Where to output generated files to", type=str, required=True
    )
    parser.add_argument(
        "--script-api-urls",
        help="A list of doc URLs to get Script API info from",
        type=str,
        default=[],
        nargs="+",
        required=True,
    )

    args = parser.parse_args()
    output = Path(args.output)

    script_api_module_info(output / "script_api", *args.script_api_urls)


def script_api_module_info(output_dir: Path, *script_api_urls: str):
    """
    Generates a file at 'output_dir' containing info about each script api module.

    `*script_api_urls` should be URLs to markdown files.
    """

    HEADER_PATTERN = re.compile(r"^---.*?---$\n", flags=re.DOTALL | re.MULTILINE)
    MANIFEST_DETAILS_PATTERN = re.compile(
        r"## Manifest Details\s```json\s(.*?)```", flags=re.MULTILINE | re.DOTALL
    )
    AVAILABLE_VERSIONS_PATTERN = re.compile(
        r"^## Available Versions\s(.*?)\s$", flags=re.MULTILINE | re.DOTALL
    )
    PRIOR_VERSIONS_PATTERN = re.compile(
        r"^### Prior Versions\s\s(?:.*\):)\s(.*?)\s$", flags=re.MULTILINE | re.DOTALL
    )
    VERSION_PATTERN = re.compile(r"`(\d+\.\d+\.\d+(?:-beta)?)`")

    modules = {}
    for name, url in ((i.split("/")[-2], i) for i in script_api_urls):
        try:
            # Try to request the data at the URL
            rq = requests.get(url)
            rq.raise_for_status()

            # Remove the header
            text = HEADER_PATTERN.sub("", rq.text)

            # Get module info if the manifest snippet exists
            module_info = {}
            if manifest := MANIFEST_DETAILS_PATTERN.search(text):
                # Parse the text further
                mainfest_json = json.loads(manifest.group(1))

                # Add the versions if they exist
                versions: list[str] = []
                if raw_versions := AVAILABLE_VERSIONS_PATTERN.search(text):
                    for m in VERSION_PATTERN.finditer(raw_versions.group(1)):
                        versions.append(m.group(1))

                # Add the prior versions if they exist
                if raw_prior_versions := PRIOR_VERSIONS_PATTERN.search(text):
                    for m in VERSION_PATTERN.finditer(raw_prior_versions.group(1)):
                        versions.append(m.group(1))

                # Create module info and add it to the dict
                module_info["module_name"] = mainfest_json["module_name"]
                module_info["versions"] = versions

                modules[name] = module_info

        except requests.HTTPError as http_ex:
            print(http_ex)

        except Exception as ex:
            print(ex)

    # Write module dict to file
    with open(output_dir / "modules.json", "w") as file:
        file.write(json.dumps(modules, indent=4))


if __name__ == "__main__":
    main()

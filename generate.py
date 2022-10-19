import argparse
from collections import defaultdict
import requests
import re
import json
import pathlib


SCRIPT_API_HEADER_PATTERN = re.compile(r'^---.*?---$\n', flags=re.DOTALL | re.MULTILINE)
SCRIPT_API_MODULE_DESCRIPTION_PATTERN = re.compile(r'^[^#>](.*)\n$', flags=re.MULTILINE)
SCRIPT_API_DEPENDENCY_PATTERN = re.compile(r'(?<=^```json)(.*?)(?=```$)', flags=re.DOTALL | re.MULTILINE)
SCRIPT_API_DEPENDENCY_COMMENT_PATTERN = re.compile(r'\/\/ .*?\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--output',
        help='Where to output generated files to',
        type=str,
        required=True
    )
    parser.add_argument(
        '--script_api_urls',
        help ='A list of doc URLs to get Gametest info from',
        type=str,
        default=[],
        nargs='+',
        required=True
    )

    args = parser.parse_args()
    output = pathlib.Path(args.output)
    script_api_urls = args.script_api_urls

    generate_script_api_module_info(script_api_urls, output/'script_api')


def generate_script_api_module_info(script_api_urls: list[str], output_dir: pathlib.Path):
    """
    Generates a file at 'ouput_dir' containing info about each script api module
    """
    # Turn each url into '(<module_name>, url)' pairs
    urls = [(i.split('/')[-2], i) for i in script_api_urls]

    # Get info from each markdown file
    module_info: dict = defaultdict(dict)
    for name, url in urls:
        try:
            rq = requests.get(url)
            rq.raise_for_status()

            # Remove the header
            text = SCRIPT_API_HEADER_PATTERN.sub('', rq.text)

            # Extract manifest dependency and remove its comment
            if match := SCRIPT_API_DEPENDENCY_PATTERN.search(text):
                dependency = json.loads(SCRIPT_API_DEPENDENCY_COMMENT_PATTERN.sub('', match.group()))
                module_info[name]['uuid'] = dependency['uuid']
                module_info[name]['version'] = dependency['version']

        except requests.HTTPError as http_ex:
            print(http_ex)
            continue
        
        except Exception as ex:
            print(ex)
            continue

    # Write module info to file
    output_dir = output_dir / 'modules.json'
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with open(output_dir, 'w+') as fp:
        fp.write(json.dumps(module_info, indent=4))


if __name__ == '__main__':
    main()

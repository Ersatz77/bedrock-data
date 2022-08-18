import argparse
import requests
import re
import json
import pathlib


GAMETEST_DEPENDENCY_PATTERN = re.compile(r'(?<=```json).*?(?=```)')
GAMETEST_DEPENDENCY_COMMENT = re.compile(r'(?<=)\/\/ .*? (?=)')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--output',
        help='Where to output generated files to',
        type=str,
        required=True
    )
    parser.add_argument(
        '--gametest_urls',
        help ='A list of doc URLs to get Gametest info from',
        type=str,
        default=[],
        nargs='+',
        required=True
    )

    args = parser.parse_args()
    output = pathlib.Path(args.output)
    gametest_urls = args.gametest_urls

    generate_gametest_module_info(gametest_urls, output/'gametest')


def generate_gametest_module_info(gametest_urls: list[str], output_dir: pathlib.Path):
    """
    Generates a file at 'ouput_dir' containing info about each gametest module
    """
    # Turn each url into '(<module_name>, url)' pairs
    urls = [(i.split('/')[-2], i) for i in gametest_urls]

    # Get info from each markdown file
    module_info: dict = {}
    for name, url in urls:
        try:
            rq = requests.get(url)
            rq.raise_for_status()

            # Make response text be on a single line
            text: str = ' '.join(rq.text.split())

            # Extract manifest dependency and remove its comment
            if match := GAMETEST_DEPENDENCY_PATTERN.search(text):
                dependency = GAMETEST_DEPENDENCY_COMMENT.sub('', match.group())
                module_info[name] = json.loads(dependency)

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

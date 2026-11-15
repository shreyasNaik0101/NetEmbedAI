"""Run the frozen offline browser adaptation pilot; never starts capture."""

import argparse

from netembed.browser_adaptation import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("data", "collection", "initial-bundle", "config", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    print(run(args.data, args.collection, args.initial_bundle, args.config, args.output))


if __name__ == "__main__":
    main()

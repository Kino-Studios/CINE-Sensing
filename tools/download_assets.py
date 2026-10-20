#!/usr/bin/env python3
"""Download the data files kept out of git from the GitHub Release matching VERSION.

Each asset lands at the path its reader expects inside this repository (or under
`--dest`). A file already present with the recorded checksum is skipped; one present
with a different checksum is refused rather than overwritten.

Usage:
    python3 tools/download_assets.py                    # every asset
    python3 tools/download_assets.py --only car.dae     # one asset (repeatable)
"""

import argparse
import hashlib
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

GITHUB_REPO = 'Kino-Studios/CINE-Sensing'
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = REPOSITORY_ROOT / 'VERSION'
CALIBRATION_IMAGES_DIRECTORY = 'tools/calibration/images'


@dataclass(frozen=True)
class Asset:
    name: str
    sha256: str | None
    destination: str


ASSETS = (
    Asset(
        'brief_k10L6.bin',
        '753e7e126c588906ad16197892bdcd914f3a0971037c8f8aeb3c63418458b035',
        'third_party/vins_fusion/loop_fusion/support_files',
    ),
    Asset(
        'car.dae',
        '54b455f828a5d85e5d586c9e3abc720c876413aaecd82940ecde5dc1150d4cac',
        'third_party/vins_fusion/global_fusion/models',
    ),
    Asset(
        'hummingbird.mesh',
        'c2b9f892fa0ec833dd9fcdf795d81fbe4b62cfed7fda05fffdf53c0ebe356641',
        'third_party/vins_fusion/global_fusion/models',
    ),
    Asset(
        'calibration.npz',
        'ef04e412415c1edc03dde57b766cdf9a20c64ee641ac3605fdecb0c3c017cb2c',
        'tools/calibration/calib_data',
    ),
    Asset(
        'calib_20251031_224257.jpg',
        'd9d8dd0eb8219da68eebc873aa3197c1cfb005c1f2f5302d48c6b59b912fb222',
        CALIBRATION_IMAGES_DIRECTORY,
    ),
    Asset(
        'calib_20251031_224314.jpg',
        '60f06153de9a8f4164b26c349690492882e4a8a4c3b2320fd27d3f57d4bbc49f',
        CALIBRATION_IMAGES_DIRECTORY,
    ),
    Asset(
        'calib_20251031_224324.jpg',
        '3b6f5d3f019d125b4836201a10377b2a0a0179875629cfdb2035058b4eeb456e',
        CALIBRATION_IMAGES_DIRECTORY,
    ),
    Asset(
        'calib_20251031_224333.jpg',
        '9c1136c3dea8cddfc3580fba51ff0c2c166450273160b73d6e9afd6cbc447805',
        CALIBRATION_IMAGES_DIRECTORY,
    ),
    Asset(
        'calib_20251031_224342.jpg',
        '51a4d872bd79034fe8849fee37242422a2e70ace7f86ebfa7cb3dfe84e56c2ca',
        CALIBRATION_IMAGES_DIRECTORY,
    ),
    Asset(
        'calib_20251031_224352.jpg',
        '85072c9141fc1b21d2b415944d22d18e188cdbcc4e950eb23257b71fa0286705',
        CALIBRATION_IMAGES_DIRECTORY,
    ),
    Asset(
        'calib_20251031_224412.jpg',
        'fad4133e18107b8969196571858cea1b5d07d59b8a287e4f04cdb3006efa4541',
        CALIBRATION_IMAGES_DIRECTORY,
    ),
    Asset(
        'calib_20251031_224441.jpg',
        '00a8850ed4e8a62519800ea11cb572b9f78d40e1f5e6480e502a1d07da95d1c0',
        CALIBRATION_IMAGES_DIRECTORY,
    ),
    Asset(
        'calib_20251031_224458.jpg',
        '98131c5f8360920f86cca1716834dba6caa081c19afdc1d74265b10c2c063477',
        CALIBRATION_IMAGES_DIRECTORY,
    ),
    Asset(
        'calib_20251031_224530.jpg',
        '5549d531c9fd57e670420c612726c495b8cb0cb087be8b66c3c2a95f99441e34',
        CALIBRATION_IMAGES_DIRECTORY,
    ),
)


class ChecksumMismatchError(Exception):
    pass


def release_tag(version_file=VERSION_FILE):
    return 'v' + Path(version_file).read_text().strip()


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as file_handle:
        for chunk in iter(lambda: file_handle.read(1 << 20), b''):
            digest.update(chunk)

    return digest.hexdigest()


def _download_with_urllib(url, target_path):
    urllib.request.urlretrieve(url, target_path)


def fetch_asset(asset, destination_root, tag, download=_download_with_urllib):
    """Place `asset` under `destination_root`, downloading it only when absent.

    Raises ChecksumMismatchError when a present file or a fresh download does not
    match the recorded checksum; a present file is never overwritten.
    """
    target_path = Path(destination_root) / asset.destination / asset.name
    if target_path.exists():
        if asset.sha256 is not None and file_sha256(target_path) != asset.sha256:
            raise ChecksumMismatchError(
                f'{target_path} exists but its sha256 is not {asset.sha256}; '
                'not overwriting it. Delete the file to download it again.'
            )

        print(f'present: {target_path}')

        return

    target_path.parent.mkdir(parents=True, exist_ok=True)
    partial_path = target_path.with_name(target_path.name + '.part')
    url = f'https://github.com/{GITHUB_REPO}/releases/download/{tag}/{asset.name}'
    print(f'downloading {url}')
    try:
        download(url, partial_path)
        if asset.sha256 is not None and file_sha256(partial_path) != asset.sha256:
            raise ChecksumMismatchError(
                f'downloaded {asset.name} does not match sha256 {asset.sha256}; discarded'
            )
    except BaseException:
        partial_path.unlink(missing_ok=True)

        raise

    partial_path.rename(target_path)
    if asset.sha256 is None:
        print(f'warning: no checksum recorded for {asset.name}; not verified')
    print(f'done: {target_path}')


def main(argv):
    asset_names = [asset.name for asset in ASSETS]
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        '--only',
        action='append',
        choices=asset_names,
        metavar='NAME',
        help=f'download only this asset (repeatable); one of: {", ".join(asset_names)}',
    )
    parser.add_argument(
        '--dest',
        type=Path,
        default=REPOSITORY_ROOT,
        help='root the asset destinations are relative to (default: this repository)',
    )
    arguments = parser.parse_args(argv)

    tag = release_tag()
    selected_assets = [
        asset for asset in ASSETS if not arguments.only or asset.name in arguments.only
    ]
    for asset in selected_assets:
        try:
            fetch_asset(asset, arguments.dest, tag)
        except (ChecksumMismatchError, OSError) as error:
            print(f'error: {error}', file=sys.stderr)

            return 1

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

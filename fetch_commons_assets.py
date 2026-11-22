#!/usr/bin/env python3
"""Download ONLY license-verified Wikimedia Commons images for 16:17.

    python fetch_commons_assets.py
    python fetch_commons_assets.py --verify-only

Standard-library networking + Pillow image decoding. Bounded retries for HTTP 429;
HTML error pages and corrupt downloads are NEVER accepted as image files.
"""
import argparse
import hashlib
import json
import os
import pathlib
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from email.utils import parsedate_to_datetime
from html import unescape

ROOT = pathlib.Path(__file__).resolve().parent
ASSET_DIR = ROOT / 'assets' / 'archival'
MANIFEST = ASSET_DIR / 'manifest.json'
API = 'https://commons.wikimedia.org/w/api.php'
HEADERS = {
    'User-Agent': '1617SchoolHistoryDocumentary/1.0 (non-commercial school project; Wikimedia Commons license audit)',
    'Accept': 'application/json,image/jpeg,image/png,*/*;q=0.5',
}
MAX_BYTES = 30 * 1024 * 1024


def real_image(data: bytes, path: pathlib.Path | None = None) -> bool:
    """Require a PNG or JPEG, optionally verified by Pillow's image decoder."""
    if not data or len(data) < 1024 or data.lstrip()[:100].lower().startswith((b'<!doctype', b'<html', b'<?xml')):
        return False
    jpeg = data.startswith(b'\xff\xd8\xff') and data.rstrip().endswith(b'\xff\xd9')
    png = data.startswith(b'\x89PNG\r\n\x1a\n') and len(data) > 33 and b'IHDR' in data[:25] and data[-8:-4] == b'IEND'
    if not (jpeg or png):
        return False
    try:
        from PIL import Image
        import io
        with Image.open(io.BytesIO(data)) as im:
            im.verify()
        with Image.open(io.BytesIO(data)) as im:
            return im.width >= 128 and im.height >= 128
    except ImportError:
        return True  # PNG/JPEG signatures and terminators already checked
    except Exception:
        return False


def fetch(url, *, retries=5, accept=None):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname not in {'commons.wikimedia.org', 'upload.wikimedia.org', 'thumb.wikimedia.org'}:
        raise ValueError('Refusing unexpected URL host: ' + url)
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={**HEADERS, **({'Accept': accept} if accept else {})})
            with urllib.request.urlopen(req, timeout=35) as r:
                ctype = r.headers.get('Content-Type', '').lower()
                data = r.read(MAX_BYTES + 1)
                if len(data) > MAX_BYTES:
                    raise RuntimeError('Image is over 30 MB limit')
                final = urllib.parse.urlsplit(r.url)
                if final.hostname not in {'commons.wikimedia.org', 'upload.wikimedia.org', 'thumb.wikimedia.org'}:
                    raise RuntimeError('Redirect target not allowed: ' + final.hostname)
                return data, ctype
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            last = exc
            code = getattr(exc, 'code', None)
            if code is not None and code not in (429, 500, 502, 503, 504):
                raise RuntimeError(f'HTTP {code}, not retryable: {url}') from exc
            if attempt + 1 == retries:
                break
            after = getattr(exc, 'headers', {}).get('Retry-After') if getattr(exc, 'headers', None) else None
            try:
                delay = max(2.0, min(120.0, float(after)))
            except (ValueError, TypeError):
                delay = min(60.0, (2 ** (attempt + 1)) * 3.5) + random.uniform(0, 1.5)
            print(f'  network limit: retry {attempt + 1}/{retries} after {delay:.1f}s', flush=True)
            time.sleep(delay)
    raise RuntimeError(f'Download failed after {retries} attempts: {last}')


def commons_info(item):
    params = {
        'action': 'query', 'prop': 'imageinfo', 'iiprop': 'url|size|mime|extmetadata',
        'titles': item['commons_title'], 'format': 'json', 'formatversion': '2',
    }
    if item.get('preferred_download_width'):
        params['iiurlwidth'] = str(item['preferred_download_width'])
    body, ctype = fetch(API + '?' + urllib.parse.urlencode(params), accept='application/json')
    if 'json' not in ctype or body.lstrip().startswith(b'<'):
        raise RuntimeError('Wikimedia API returned non-JSON content')
    pages = json.loads(body)['query']['pages']
    if not pages or pages[0].get('missing'):
        raise RuntimeError('Commons title missing: ' + item['commons_title'])
    info = pages[0].get('imageinfo', [])
    if not info:
        raise RuntimeError('Commons imageinfo missing: ' + item['commons_title'])
    return info[0]


def validate_license(info, item):
    meta = info.get('extmetadata', {})
    def field(key):
        return unescape(re.sub('<[^>]*>', '', str(meta.get(key, {}).get('value', '')))).strip()
    license_name = field('LicenseShortName')
    usage = field('UsageTerms')
    license_tag = field('License')
    permitted = ('public domain' in license_name.lower() or license_tag.lower() in ('pd','cc0','cc-by','cc-by-sa')
                 or license_name.lower().startswith(('cc by ', 'cc by-sa ', 'cc0 ')))
    if not permitted or item['license_family'].lower() != 'public domain' or 'public domain' not in license_name.lower():
        raise RuntimeError(f'LICENSE RECHECK FAILED: {license_name!r} {license_tag!r} {usage!r}')
    return license_name, field('Artist')


def run():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dest', type=pathlib.Path, default=ASSET_DIR, help='Target directory, defaults to assets/archival')
    ap.add_argument('--only', help='Asset ID (e.g. s04_revolutionaries_1921)')
    ap.add_argument('--verify-only', action='store_true', help='Offline verification: do not contact Wikimedia')
    ap.add_argument('--delay', type=float, default=3.0, help='Polite seconds between successful image requests')
    ap.add_argument('--retries', type=int, default=5, help='Max HTTP attempts per request')
    args = ap.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    images = [i for i in manifest['approved_assets'] if not args.only or i['id'] == args.only]
    if not images:
        ap.error('No asset matches --only')
    args.dest.mkdir(parents=True, exist_ok=True)
    successes, failures = [], []
    for item in images:
        path = args.dest / item['filename']
        print(f"[{item['scene']}] {item['filename']}", flush=True)
        if path.is_file() and real_image(path.read_bytes()):
            print(f'  verified existing image, size={path.stat().st_size} bytes')
            successes.append(item['filename'])
            continue
        if args.verify_only:
            print('  MISSING OR INVALID')
            failures.append(item['filename'])
            continue
        try:
            info = commons_info(item)
            lic, artist = validate_license(info, item)
            url = info.get('thumburl') or info.get('url')
            if not url:
                raise RuntimeError('No Commons download URL')
            data, ctype = fetch(url, retries=args.retries, accept='image/jpeg,image/png')
            if 'image' not in ctype or not real_image(data):
                raise RuntimeError(f'Invalid image response (type={ctype!r}, bytes={len(data)}); HTML/rate limit body rejected')
            want_jpeg = path.suffix.lower() in ('.jpeg', '.jpg')
            if want_jpeg != data.startswith(b'\xff\xd8\xff'):
                raise RuntimeError('File format mismatches target extension')
            temp = path.with_suffix(path.suffix + '.download')
            temp.write_bytes(data)
            if not real_image(temp.read_bytes()):
                temp.unlink(missing_ok=True)
                raise RuntimeError('Temporary file verification failed')
            os.replace(temp, path)
            print(f'  OK / {len(data)} bytes / {lic}')
            successes.append(item['filename'])
            time.sleep(max(0, args.delay))
        except Exception as exc:
            print(f'  FAILED (not installed): {exc}', file=sys.stderr, flush=True)
            failures.append(item['filename'])
    report={'downloaded_or_verified':successes,'missing_or_invalid':failures}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(run())

"""Approved archival assets, read from assets/archival/manifest.json
(director pack v2). A file is used only if it is a verified JPEG/PNG; the
caption always states painting vs photograph, author and date."""
import json
import os

from .common import PROJECT_ROOT

ARCH_DIR = os.path.join(PROJECT_ROOT, "assets", "archival")
AUTHOR_MN = {   # on-screen Mongolian credit (English originals stay in manifest.json)
    "s02_chinggis_yuan_portrait": "Юань үеийн үл мэдэгдэх зураач (Тайпэй, Үндэсний ордны музей)",
    "s03_bogd_sharav": "Марзан Шарав",
    "s03_gandan_1913": "Стефан Пассе (Альбер Каны музей)",
    "s03_tsagaan_hill_1913": "Стефан Пассе (Альбер Каны музей)",
    "s04_revolutionaries_1921": "Гэрэл зурагчин тодорхойгүй",
    "s04_kyakhta_1921": "Гэрэл зурагчин тодорхойгүй",
}
_MANIFEST = None


def manifest():
    """Approved Commons assets (director pack v2) + Albert-Kahn CC0 autochromes."""
    global _MANIFEST
    if _MANIFEST is None:
        with open(os.path.join(ARCH_DIR, "manifest.json"), encoding="utf-8") as fh:
            _MANIFEST = {a["id"]: a for a in json.load(fh)["approved_assets"]}
        ak = os.path.join(ARCH_DIR, "albert_kahn.json")
        if os.path.exists(ak):
            for a in json.load(open(ak, encoding="utf-8"))["assets"]:
                _MANIFEST[a["id"]] = {
                    "id": a["id"], "filename": a["filename"], "scene": a["scene"], "role": a["role"],
                    "display_title": a["caption_mn"].split(" — ")[0].replace("\n", " "), "caption_mn": a["caption_mn"],
                    "author": f"{a['author']}; Musée Albert-Kahn {a['inventory']}",
                    "date": a["place_date"], "license_label": f"{a['licence']} (Musée départemental Albert-Kahn)",
                    "commons_page": a["page"], "source": "albert-kahn"}
                AUTHOR_MN[a["id"]] = f"Стефан Пассе · Альбер Каны музей ({a['inventory']})"
    return _MANIFEST


def first_available(*ids):
    """First asset id in priority order whose file is a verified image."""
    for i in ids:
        if i in manifest() and asset(i)["path"]:
            return i
    return ids[0]


def verified(path):
    if not os.path.isfile(path) or os.path.getsize(path) < 1024:
        return False
    with open(path, "rb") as fh:
        data = fh.read()
    jpeg = data[:3] == b"\xff\xd8\xff" and data.rstrip().endswith(b"\xff\xd9")
    png = data[:8] == b"\x89PNG\r\n\x1a\n"
    return jpeg or png


def asset(asset_id):
    """-> dict(path or None, caption, credit, role) for an approved asset id."""
    a = manifest()[asset_id]
    path = os.path.join(ARCH_DIR, a["filename"])
    author = AUTHOR_MN.get(asset_id, a["author"].split(";")[0].strip())
    return {
        "path": path if verified(path) else None,
        "caption": a["caption_mn"],
        "credit": (f"{author} · CC0, нийтийн өмч" if a.get("source") == "albert-kahn"
                   else f"{author} · Wikimedia Commons · Нийтийн өмч"),
        "role": a["role"],
        "entry": a,
    }


def credits_lines():
    out = []
    for a in manifest().values():
        if not verified(os.path.join(ARCH_DIR, a["filename"])):
            continue
        out.append(f"{a['display_title']} — {a['author'].split(';')[0].strip()}, {a['date'].split('(')[0].strip()}"
                   f" · {a['license_label'].split('(')[0].strip()} · {a['commons_page'].replace('https://', '')}")
    return out

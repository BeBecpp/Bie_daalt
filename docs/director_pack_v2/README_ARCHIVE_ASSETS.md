# 16:17 — Архивын зургийн бэлэн интеграци

> 2026-11-22. **Анхаарах:** Энэхүү багцад лиценз нь шалгагдсан 6 архивын зураг/хөргийн нэр, Wikimedia Commons дахь эх холбоос, attribution, scene mapping болон зураг татагч код багтсан. Эндээс Wikimedia-ийн binary JPEG/PNG татах сүлжээ хаалттай байсан тул **бодит JPG/PNG файл ZIP-д хийгдээгүй**. Үүсгэсэн гэж худал тэмдэглээгүй. `fetch_commons_assets.py`-г интернэттэй компьютерт ажиллуулахад шаардлагатай бодит зургууд автоматаар `assets/archival/` руу орно.

## Нэг удаа ажиллуулах

Windows PowerShell:

```powershell
py -m pip install Pillow
py fetch_commons_assets.py
py fetch_commons_assets.py --verify-only
```

Linux/Mac:

```bash
python3 -m pip install pillow
python3 fetch_commons_assets.py
python3 fetch_commons_assets.py --verify-only
```

Файл бүрийг **Wikimedia Commons-ийн API-аас** дахин шалгаж татна. `LicenseShortName=Public domain` бус бол зургийг суулгахгүй. HTTP 429 алдаатай HTML файлыг жинхэнэ зураг гэж андуурахгүй. `--verify-only` бүгд OK бол exit code `0` гарна. Wikimedia дахин rate-limit хийвэл зогсоож, дараа нь зөвхөн дутуу asset-аа: `python fetch_commons_assets.py --only s03_gandan_1913` гэж ажиллуулж болно. Хэрэглэгчийн олон зураг/суусан файлд гар хүрэхгүй.

## Аль хэсэгт аль файл?

| Scene | Файл | Дүрслэл |
|---|---|---|
| 02 — 1206 | `s02_chinggis_yuan_portrait.jpg` | Юань үеийн Чингис хааны **уран зураг**. 1206 онд авсан зураг биш |
| 03 — 1911 | `s03_bogd_sharav.jpg` | Марзан Шаравын Богд хааны **уран зураг** |
| 03 — 1911 | `s03_gandan_1913.jpg` | 1913 оны Гандангийн **жинхэнэ гэрэл зураг** — 1911 оны үйл явдлын яг тэр мөчийг харуулахгүй, үеийн орчныг үзүүлнэ |
| 03 — 1911 | `s03_tsagaan_hill_1913.jpg` | 1913 оны Цагаан толгой / Нийслэл хүрээний **жинхэнэ өнгөт гэрэл зураг** |
| 04 — 1921 | `s04_revolutionaries_1921.jpg` | 1921 оны 9-р сарын Монголын хувьсгалчдын **жинхэнэ гэрэл зураг** |
| 04 — 1921 | `s04_kyakhta_1921.jpg` | 1921 оны 3-р сарын Ар Хиагтын **жинхэнэ гэрэл зураг** |

1924 оны анхдугаар Их Хурлын жинхэнэ зураг Commons-д байгаа боловч АНУ-д эрх нь дууссан гэж тайлбарласан тусдаа тэмдэглэгээ нь дутуу. Энэ багц тухайн зургийг автоматаар татахгүй — эх файлын эрхийг тусад нь дахин баталгаажуулах хэрэгтэй. 1924 оны Үндсэн хуулийн сканыг ч зөвшөөрөлгүйгээр ашиглаагүй.

## Blender / Claude интеграц

`blender_archival_card.py` нь архивын зургийг 3D хавтгай дээр texture болгон байрлуулж, зөөлөн parallax хөдөлгөөн өгдөг helper юм. Энэ нь кино бичлэг биш тул дэлгэцэнд бодит archival photography гэсэн caption хадгал. Scene кодын render pipeline-г өөрчлөхгүйгээр оруулж болно:

```python
from blender_archival_card import add_archive_photo, verified_asset
path = verified_asset('s04_revolutionaries_1921.jpg')
if path is not None:
    add_archive_photo(path, name='Mongolian Revolutionaries — 1921', start_frame=1, end_frame=144)
```

Таны Scene 03, Scene 04-ийн одоогийн код өөр хавтас, материалын системтэй байж болно. Тиймээс `ASSET_MANIFEST.md`-ийг Claude Code-д уншуулаад **одоогийн сцений кодыг хадгалж**, зураг оруулах цэгийг интеграц хийлгэ. Хоосон placeholder эсвэл rate-limit HTML-г texture гэж бүү ашигла.

## Лиценз ба кредит

`assets/archival/LICENSES_AND_CREDITS.md` — зураг бүрийн Commons эх хуудас, эрхийн үндэслэл, зохиогч, огноо, onscreen caption.

`assets/archival/onscreen_captions.srt` — эвлүүлэг хийхэд ашиглах Монгол credit subtitle. Текстийн цагийг эцсийн монтажтай тааруул.

`preview_archives.html` — интернеттэй browser-т нээж 6 визуал референс харах хуудас; алсаас ачаалдаг зураг нь ZIP доторх локал JPG гэсэн үг биш.

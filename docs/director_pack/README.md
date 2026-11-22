# 16:17 — Republic Day Cinematic Documentary
**10-р ангийн Монголын түүхийн бие даалтын режиссёрын багц**
**Түвшин:** stylized historical documentary, 3D + archival mixed media
**Зорилтот видео:** 3:45–4:15, 1920×1080, 24fps, MP4 H.264 / AAC
**Хугацааны гол сэдэв:** 1924.11.26 — 16:17
**Хэл:** Монгол кирилл субтитр, Монгол хэлээр дуу оруулалт

## Гол санаа
Кино 1924 оны 16:17 минут дээр эхэлж, цаг хугацааг 1206 → 1911 → 1921 → 1924 болгон ухраан/урагшлуулан харуулна. Үндсэн хуулийн бодит эх бичиг ба архивын зурагт түшиглэнэ. Өнгөрсөн үеийн 3D сэргээн дүрслэлүүдийг **'Уран сайхны сэргээн дүрслэл'** хэмээн тэмдэглэнэ.

## Энэ багцын файлууд
- CLAUDE.md — Claude Code-д ажлын журам, шаардлага, build acceptance criteria
- 01_storyboard.md — 8 хэсэг, камер, динамик, гэрэл, дуу
- 02_narration_mn.md — бэлэн Монгол voice-over
- 03_fact_check_sources.md — баталгаатай эх сурвалж, анхааруулга
- 04_pipeline.md — Blender / Kdenlive / FFmpeg / ElevenLabs workflow
- 05_art_direction.md — өнгө, гэрэлтүүлэг, дүрслэл ба дуу
- 06_asset_credits.md — эх сурвалж/эрхийн бүртгэл
- 07_start_with_claude.txt — Claude-д шууд өгөх эхний хүсэлт
- shots.json — scenes, duration, visual priorities

## Анхлан ажиллуулах
1) Claude Code-д энэ фолдерыг төслийн суурь context болгон нээ.
2) `07_start_with_claude.txt` файлыг Claude-д өг.
3) Claude-аар эхлээд зөвхөн 7–10 секундийн Scene 01 preview буюу POC-ийг ажиллуулж шалга.
4) Урьдчилсан богино rendering баталгаажмагц бүх үзэгдэлд шилж.
5) ElevenLabs дээр сцен бүрийг тусад нь бүтээ; `/audio/` дотор WAV хадгал.
6) Kdenlive эсвэл FFmpeg-аар эцсийн MP4, optional SRT гарга.

**Анхаарах:** Энэ ZIP бол судалгаа, зохиол, техникийн даалгавартай director pack; бэлэн render хийсэн 3D кино биш.

#!/usr/bin/env python3
# 定时从抖音合集接口抓取，产出两个文件：
#   direct.json   —— 每集的「直链 + 时长」（投屏全速用）
#   episodes.json —— 剧集清单（工作台自动入库用）
# 新增一季：在 MIX_IDS 里加一条即可；include 可限定只取某几集（如 [25,33]）
import json, os, ssl, sys, datetime, urllib.request

DEFAULT_MIXES = [
    {"id": "7669019617909540899", "season": 1, "include": [[25, 33]]},
    {"id": "7670150022856214564", "season": 2}
]
MIXES = json.loads(os.environ.get("MIX_IDS", "null")) or DEFAULT_MIXES
UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
ctx = ssl.create_default_context()

def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return json.load(urllib.request.urlopen(req, timeout=timeout, context=ctx))

def in_range(ep, include):
    if not include:
        return True
    for a, b in include:
        if ep is not None and a <= ep <= b:
            return True
    return False

eps_direct = {}
episodes = []

for m in MIXES:
    mix, season, include = m["id"], m.get("season", 1), m.get("include")
    cursor, page, got = 0, 0, 0
    while True:
        u = ("https://www.iesdouyin.com/aweme/v1/mix/aweme/?mix_id=%s&aid=1128"
             "&count=30&cursor=%s&device_platform=webapp" % (mix, cursor))
        try:
            d = fetch(u)
        except Exception as e:
            print("!! 抓取失败 mix=%s cursor=%s : %s" % (mix, cursor, e), file=sys.stderr)
            break
        lst = d.get("aweme_list") or []
        if not lst:
            break
        try:
            ep_map = json.loads(d.get("item_id_to_episode") or "{}")
        except Exception:
            ep_map = {}
        for a in lst:
            v = a.get("video") or {}
            pa = v.get("play_addr") or {}
            vid = pa.get("uri")
            ul = pa.get("url_list") or []
            if not vid or not ul:
                continue
            dur = a.get("duration") or v.get("duration") or 0
            sec = int(round(dur / 1000)) if dur else None
            num = ep_map.get(str(a.get("aweme_id")))
            aweme = str(a.get("aweme_id"))
            # 直链：全部收录（供投屏使用）
            eps_direct[vid] = {"url": ul[0], "sec": sec, "ep": num,
                               "aweme": aweme, "mix": mix, "season": season}
            # 清单：只收录配置范围内的
            if not in_range(num, include):
                continue
            episodes.append({
                "id": "s%d-%02d" % (season, num or 0),
                "season": season,
                "number": str(num if num is not None else ""),
                "title": "Wow English 第%s季 第%s集" % ("一" if season == 1 else ("二" if season == 2 else season), num),
                "src": "douyin",
                "videoId": vid,
                "awemeId": aweme,
                "sec": sec
            })
            got += 1
        if not d.get("has_more"):
            break
        cursor = d.get("cursor") or (cursor + len(lst))
        page += 1
        if page > 25:
            break
    print("第%s季 合集 %s：入库 %s 集" % (season, mix, got))

now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
episodes.sort(key=lambda x: (x["season"], int(x["number"] or 0)))

with open("direct.json", "w", encoding="utf-8") as f:
    json.dump({"updated": now, "mixes": [m["id"] for m in MIXES], "eps": eps_direct},
              f, ensure_ascii=False, indent=1)
with open("episodes.json", "w", encoding="utf-8") as f:
    json.dump({"updated": now, "eps": episodes}, f, ensure_ascii=False, indent=1)
print("直链 %d 条 / 剧集 %d 集" % (len(eps_direct), len(episodes)))

#!/usr/bin/env python3
# 自动从抖音合集接口取每集的「直链 + 时长」，写成 direct.json
# 由 GitHub Actions 定时执行；新增/更换合集只需改 MIX_IDS
import json, os, ssl, sys, datetime, urllib.request

MIX_IDS = json.loads(os.environ.get("MIX_IDS", '["7669019617909540899"]'))
UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
ctx = ssl.create_default_context()

def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return json.load(urllib.request.urlopen(req, timeout=timeout, context=ctx))

eps = {}
for mix in MIX_IDS:
    cursor, page = 0, 0
    while True:
        u = ("https://www.iesdouyin.com/aweme/v1/mix/aweme/?mix_id=%s&aid=1128"
             "&count=30&cursor=%s&device_platform=webapp" % (mix, cursor))
        try:
            d = fetch(u)
        except Exception as e:
            print("!! 取集合失败 mix=%s cursor=%s : %s" % (mix, cursor, e), file=sys.stderr)
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
            eps[vid] = {
                "url": ul[0],
                "sec": int(round(dur / 1000)) if dur else None,
                "ep": ep_map.get(str(a.get("aweme_id"))),
                "aweme": str(a.get("aweme_id")),
                "mix": mix
            }
        if not d.get("has_more"):
            break
        cursor = d.get("cursor") or (cursor + len(lst))
        page += 1
        if page > 25:
            break

out = {
    "updated": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "mixes": MIX_IDS,
    "eps": eps
}
with open("direct.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("已写入 direct.json，共 %d 集" % len(eps))

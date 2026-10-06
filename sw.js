// 中转脚本（仅用于测速验证方案C）：把本域名下的 /__p/xxx.mp4 请求转去取抖音的视频流
self.addEventListener('install', function(e){ self.skipWaiting(); });
self.addEventListener('activate', function(e){ e.waitUntil(self.clients.claim()); });

var EPS = {
  '025': {v:'v0300fg10000d9k7utnog65s79brsv7g', l:0},
  '026': {v:'v0300fg10000d9kudfnog65rlkr8br8g', l:0},
  '027': {v:'v0300fg10000d9kvc4vog65hotcem630', l:0},
  '028': {v:'v0300fg10000d9lhbefog65ofmnek4k0', l:0},
  '029': {v:'v0300fg10000da60lvfog65n66njripg', l:1},
  '030': {v:'v0300fg10000d9m9h5vog65vlupu1g00', l:0},
  '031': {v:'v0300fg10000d9ma2hvog65mgb2r5o60', l:0},
  '032': {v:'v0300fg10000d9mt49vog65qfmrlnqg0', l:0},
  '033': {v:'v0300fg10000d9mubpfog65njagdv0dg', l:1}
};

self.addEventListener('fetch', function(e){
  var u = new URL(e.request.url);
  var m = u.pathname.match(/\/__p\/(\d+)\.mp4$/);
  if(!m) return;
  var ep = EPS[m[1]];
  if(!ep) return;
  var target = 'https://aweme.snssdk.com/aweme/v1/playwm/?video_id=' + ep.v + '&ratio=540p&line=' + ep.l;
  e.respondWith(
    fetch(target, {redirect:'follow', mode:'cors'}).then(function(r){
      return new Response(r.body, {
        status: 200,
        headers: {'Content-Type':'video/mp4'}
      });
    }).catch(function(err){
      return new Response('proxy error: ' + err, {status:502});
    })
  );
});

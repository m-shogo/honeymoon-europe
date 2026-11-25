// チェックリストとメモを、この端末のブラウザにだけ保存する。
(function () {
  var page = document.body.getAttribute("data-page") || "page";
  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) { /* 保存できない環境でも表示は続ける */ } }
  };
  document.querySelectorAll("input[type=checkbox][data-k]").forEach(function (box) {
    var key = "techo:" + page + ":" + box.getAttribute("data-k");
    box.checked = store.get(key) === "1";
    box.addEventListener("change", function () { store.set(key, box.checked ? "1" : "0"); });
  });
  document.querySelectorAll("textarea[data-memo]").forEach(function (area) {
    var key = "techo:" + page + ":memo:" + area.getAttribute("data-memo");
    area.value = store.get(key) || "";
    var t;
    area.addEventListener("input", function () {
      clearTimeout(t);
      t = setTimeout(function () { store.set(key, area.value); }, 300);
    });
  });

  // 写真の帯・ページ内メニューから、その場所／欄を開いて移動
  function openTarget(id) {
    var el = document.getElementById(id);
    if (!el) return;
    var d = el.tagName === "DETAILS" ? el : el.querySelector("details");
    if (d) d.open = true;
    el.scrollIntoView({ behavior: "smooth", block: "start" });
    if (history.replaceState) history.replaceState(null, "", "#" + id);
  }
  document.querySelectorAll("[data-open]").forEach(function (a) {
    a.addEventListener("click", function (ev) { ev.preventDefault(); openTarget(a.getAttribute("data-open")); });
  });
  if (location.hash.length > 1) { var h = location.hash.slice(1); if (document.getElementById(h)) setTimeout(function () { openTarget(h); }, 50); }

  // 詳細の最後の「閉じる」：閉じて、その項目の位置に戻る
  document.querySelectorAll("[data-close]").forEach(function (b) {
    b.addEventListener("click", function () {
      var d = b.closest("details"); if (!d) return;
      d.open = false;
      var li = d.parentElement; if (li && li.scrollIntoView) li.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });


  // ひとことフレーズ：場面で絞り込み
  document.querySelectorAll(".pr-tabs").forEach(function (box) {
    box.addEventListener("click", function (ev) {
      var b = ev.target.closest("button"); if (!b) return;
      box.querySelectorAll("button").forEach(function (x) { x.classList.toggle("on", x === b); });
      var cat = b.getAttribute("data-cat");
      box.parentElement.querySelectorAll(".pr").forEach(function (r) {
        r.hidden = cat === "today" ? r.getAttribute("data-focus") !== "1" : (cat !== "all" && r.getAttribute("data-cat") !== cat);
      });
    });
  });

  // 読み上げ：やわらかい自然な声を優先。低い声・効果音的な声（Whisper, Bad News など）は使わない
  var PREFER = {
    it: ["Alice", "Federica", "Emma", "Elsa", "Isabella", "Google italiano", "Microsoft Elsa"],
    es: ["Mónica", "Monica", "Marisol", "Paulina", "Helena", "Google español", "Microsoft Helena", "Microsoft Elvira"],
    fr: ["Audrey", "Amélie", "Amelie", "Marie", "Aurélie", "Google français", "Microsoft Denise", "Microsoft Julie"],
    en: ["Samantha", "Ava", "Allison", "Susan", "Karen", "Google US English", "Microsoft Aria", "Microsoft Jenny", "Microsoft Zira"]
  };
  var AVOID = /(Whisper|Bad News|Good News|Bahh|Bells|Boing|Bubbles|Cellos|Jester|Organ|Superstar|Trinoids|Wobble|Zarvox|Albert|Fred|Junior|Ralph|Kathy|Grandpa|Grandma|Rocko|Shelley|Eddy|Reed|Sandy|Flo|Deranged|Hysterical|Pipe Organ|Luca|Jorge|Diego|Thomas|Jacques|Daniel|Alex|Aaron|Arthur|Nicolas|Diego)/i;
  var voices = [];
  function loadVoices() { try { voices = window.speechSynthesis.getVoices() || []; } catch (e) { voices = []; } }
  function pickVoice(lang) {
    var base = lang.slice(0, 2);
    var cand = voices.filter(function (v) { return v.lang && v.lang.replace("_", "-").toLowerCase().indexOf(base) === 0 && !AVOID.test(v.name); });
    if (!cand.length) return null;
    function score(v) {
      var s = 0, pref = PREFER[base] || [];
      for (var i = 0; i < pref.length; i++) if (v.name.indexOf(pref[i]) >= 0) { s += 100 - i; break; }
      if (/premium|enhanced|natural|neural/i.test(v.name)) s += 30;
      if (v.lang.replace("_", "-").toLowerCase() === lang.toLowerCase()) s += 10;
      if (v.localService) s += 2;
      return s;
    }
    cand.sort(function (a, b) { return score(b) - score(a); });
    return cand[0];
  }
  if ("speechSynthesis" in window) {
    loadVoices();
    if (window.speechSynthesis.addEventListener) window.speechSynthesis.addEventListener("voiceschanged", loadVoices);
  } else {
    document.body.classList.add("no-tts");
  }
  document.querySelectorAll(".say").forEach(function (b) {
    b.addEventListener("click", function () {
      try {
        if (!voices.length) loadVoices();
        var lang = b.getAttribute("data-lang");
        var text = b.getAttribute("data-say").replace(/\s*\/\s*/g, ", ").replace(/…/g, "");
        var u = new SpeechSynthesisUtterance(text);
        u.lang = lang;
        var v = pickVoice(lang); if (v) u.voice = v;
        u.rate = 0.95; u.pitch = 1.1;
        window.speechSynthesis.cancel(); window.speechSynthesis.speak(u);
        b.classList.add("on"); u.onend = function () { b.classList.remove("on"); };
      } catch (e) { /* 読み上げに対応しない端末では何もしない */ }
    });
  });

  // すべて開く／閉じる
  var allBtn = document.querySelector("[data-toggle-all]");
  if (allBtn) allBtn.addEventListener("click", function () {
    var items = document.querySelectorAll(".tl2 details");
    var open = allBtn.textContent.indexOf("開く") >= 0;
    items.forEach(function (d) { d.open = open; });
    allBtn.textContent = open ? "すべて閉じる" : "すべて開く";
  });

  // 上へボタン
  var top = document.querySelector(".totop");
  if (top) {
    var onScroll = function () { top.classList.toggle("show", window.scrollY > 700); };
    window.addEventListener("scroll", onScroll, { passive: true }); onScroll();
    top.addEventListener("click", function (ev) { ev.preventDefault(); window.scrollTo({ top: 0, behavior: "smooth" }); });
  }

  // 今いる欄をメニューで強調
  var links = Array.prototype.slice.call(document.querySelectorAll(".subnav a"));
  if (links.length && "IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (en) {
        if (!en.isIntersecting) return;
        links.forEach(function (l) { l.classList.toggle("on", l.getAttribute("data-open") === en.target.id); });
      });
    }, { rootMargin: "-130px 0px -60% 0px" });
    links.forEach(function (l) { var t = document.getElementById(l.getAttribute("data-open")); if (t) io.observe(t); });
  }
  // ← → キーで前後の日へ
  document.addEventListener("keydown", function (ev) {
    if (/input|textarea/i.test((ev.target || {}).tagName || "")) return;
    var sel = ev.key === "ArrowLeft" ? ".next a:first-child" : ev.key === "ArrowRight" ? ".next a.r" : null;
    var a = sel && document.querySelector(sel);
    if (a) location.href = a.getAttribute("href");
  });

  // ---------- 今日（旅行中は今日のページへ、出発前はカウントダウン）
  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function tripInfo(el) {
    var st = (el.getAttribute("data-start") || "").split("-"), days = +el.getAttribute("data-days");
    var start = new Date(+st[0], +st[1] - 1, +st[2]);
    var now = new Date(); var today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    var diff = Math.round((today - start) / 86400000);
    return { diff: diff, days: days, n: diff + 1 };
  }
  var tl = document.querySelector("[data-today]");
  if (tl) {
    var ti = tripInfo(tl);
    if (ti.diff >= 0 && ti.diff < ti.days) {
      tl.href = "day" + pad(ti.n) + ".html"; tl.textContent = "今日 DAY" + pad(ti.n); tl.hidden = false;
    } else if (ti.diff < 0 && ti.diff > -120) {
      tl.href = "day01.html"; tl.textContent = "出発まで" + (-ti.diff) + "日"; tl.hidden = false;
    }
  }
  var tb = document.querySelector("[data-todaybar]");
  if (tb) {
    var t2 = tripInfo(tb), html;
    if (t2.diff >= 0 && t2.diff < t2.days) {
      html = '<a class="todaybar__go" href="day' + pad(t2.n) + '.html"><small>Today</small><b>今日は DAY ' + pad(t2.n) + '</b><span>今日のページを開く →</span></a>';
    } else if (t2.diff < 0) {
      html = '<a class="todaybar__go" href="day01.html"><small>Countdown</small><b>出発まで あと ' + (-t2.diff) + ' 日</b><span>1/31（日）22:55 羽田発 ／ DAY01を開く →</span></a>';
    } else {
      html = '<a class="todaybar__go" href="day13.html"><small>Welcome home</small><b>おかえりなさい</b><span>13日間のアルバムへ →</span></a>';
    }
    tb.innerHTML = html;
  }

  // ---------- 予約済みの印（スポットIDごと。表紙・各日で連動）
  function bookKey(id) { return "techo:booked:" + id; }
  function paintBooked() {
    document.querySelectorAll("[data-book]").forEach(function (el) {
      el.classList.toggle("booked", store.get(bookKey(el.getAttribute("data-book"))) === "1");
    });
    document.querySelectorAll("[data-book-toggle]").forEach(function (b) {
      b.checked = store.get(bookKey(b.getAttribute("data-book-toggle"))) === "1";
    });
    var sum = document.querySelector("[data-book-sum]");
    if (sum) {
      var all = document.querySelectorAll(".bk"), done = document.querySelectorAll(".bk.booked").length;
      sum.innerHTML = "<b>" + done + " / " + all.length + "</b> 予約済み";
    }
  }
  document.querySelectorAll("[data-book-toggle]").forEach(function (b) {
    b.addEventListener("click", function (ev) { ev.stopPropagation(); });
    b.addEventListener("change", function () {
      store.set(bookKey(b.getAttribute("data-book-toggle")), b.checked ? "1" : "0");
      paintBooked();
    });
  });
  // 発売日まで何日か
  document.querySelectorAll("[data-open-date]").forEach(function (el) {
    var p = el.getAttribute("data-open-date").split("-");
    var d = new Date(+p[0], +p[1] - 1, +p[2]), now = new Date();
    var days = Math.ceil((d - new Date(now.getFullYear(), now.getMonth(), now.getDate())) / 86400000);
    el.textContent += days <= 0 ? "（発売中のはず・早めに）" : "（あと" + days + "日）";
    el.classList.toggle("now", days <= 7);
  });
  paintBooked();

  // ---------- ホテル住所カード
  var dlg = document.getElementById("hotel-dlg");
  function hotelKey(c) { return "techo:hotel:" + c; }
  function readHotel(c) { try { return JSON.parse(store.get(hotelKey(c)) || "{}"); } catch (e) { return {}; } }
  function labelHotels() {
    document.querySelectorAll("[data-hotel]").forEach(function (chip) {
      var h = readHotel(chip.getAttribute("data-hotel"));
      var lab = chip.querySelector("[data-hotel-label]");
      if (lab) lab.textContent = h.name ? h.name : "ホテルを登録する";
      chip.classList.toggle("set", !!h.name);
    });
  }
  labelHotels();
  if (dlg) {
    var curChip = null;
    var form = dlg.querySelector("form");
    var v = function (k) { return dlg.querySelector('[data-v="' + k + '"]'); };
    function showView() {
      var c = curChip.getAttribute("data-hotel"), h = readHotel(c);
      v("city").textContent = curChip.getAttribute("data-city-name") + "のホテル";
      v("phrase").textContent = curChip.getAttribute("data-phrase");
      v("phrase-en").textContent = curChip.getAttribute("data-phrase-en");
      v("name").textContent = h.name || ""; v("addr").textContent = h.addr || ""; v("tel").textContent = h.tel || "";
      v("map").href = "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent((h.name || "") + " " + (h.addr || ""));
      dlg.classList.remove("editing");
    }
    function showEdit() {
      var c = curChip.getAttribute("data-hotel"), h = readHotel(c);
      v("city2").textContent = curChip.getAttribute("data-city-name");
      form.name.value = h.name || ""; form.addr.value = h.addr || ""; form.tel.value = h.tel || "";
      dlg.classList.add("editing");
    }
    function openDlg() {
      if (dlg.showModal) dlg.showModal(); else dlg.setAttribute("open", "");
    }
    function closeDlg() { if (dlg.close) dlg.close(); else dlg.removeAttribute("open"); }
    document.querySelectorAll("[data-hotel]").forEach(function (chip) {
      chip.addEventListener("click", function () {
        curChip = chip;
        if (readHotel(chip.getAttribute("data-hotel")).name) showView(); else showEdit();
        openDlg();
      });
    });
    dlg.addEventListener("click", function (ev) {
      var b = ev.target.closest("[data-hd]"); if (!b) { if (ev.target === dlg) closeDlg(); return; }
      var act = b.getAttribute("data-hd");
      if (act === "close") closeDlg();
      if (act === "edit") showEdit();
      if (act === "save") {
        var h = { name: form.name.value.trim(), addr: form.addr.value.trim(), tel: form.tel.value.trim() };
        store.set(hotelKey(curChip.getAttribute("data-hotel")), JSON.stringify(h));
        labelHotels(); showView();
      }
    });
  }

  // ---------- オフライン保存
  var offState = document.querySelector("[data-offline-state]");
  function say(msg) { if (offState) offState.textContent = msg; }
  if ("serviceWorker" in navigator && location.protocol !== "file:") {
    navigator.serviceWorker.register("sw.js").then(function () {
      return navigator.serviceWorker.ready;
    }).then(function () {
      if (document.querySelector('[data-offline="day"]')) countSaved();
    }).catch(function () { say("このブラウザでは電波なしで見るための保存が使えません。"); });
  } else {
    say("このブラウザでは電波なしで見るための保存が使えません。");
  }
  function pageImages(doc) {
    return Array.prototype.map.call((doc || document).querySelectorAll("img[src^='https://upload.wikimedia.org']"), function (i) { return i.getAttribute("src"); })
      .filter(function (u, i, a) { return a.indexOf(u) === i; });
  }
  function countSaved() {
    if (!window.caches) return;
    var urls = pageImages();
    caches.open("techo-media").then(function (c) {
      return Promise.all(urls.map(function (u) { return c.match(u).then(function (r) { return !!r; }); }));
    }).then(function (r) {
      var n = r.filter(Boolean).length;
      say(n >= urls.length ? "✓ この日の写真はすべて保存済み。電波がなくても見られます（地図は通信が必要）。"
                           : "文字とデザインは保存済み。写真は " + n + " / " + urls.length + " 枚を保存済み。");
    });
  }
  function saveUrls(urls, btn, bar) {
    if (!window.caches) { say("このブラウザでは保存できません。"); return Promise.resolve(); }
    btn.disabled = true; var done = 0, fail = 0;
    if (bar) { bar.hidden = false; bar.max = urls.length; bar.value = 0; }
    return caches.open("techo-media").then(function (c) {
      var i = 0;
      function next() {
        if (i >= urls.length) return Promise.resolve();
        var u = urls[i++];
        return c.match(u).then(function (hit) {
          if (hit) return;
          return fetch(u, { mode: "cors", credentials: "omit" }).then(function (r) { if (r.ok) return c.put(u, r); fail++; }).catch(function () { fail++; });
        }).then(function () {
          done++; if (bar) bar.value = done;
          say("写真を保存中… " + done + " / " + urls.length);
          return new Promise(function (res) { setTimeout(res, 120); }).then(next);
        });
      }
      return Promise.all([next(), next(), next()]);
    }).then(function () {
      btn.disabled = false;
      say(fail ? "保存しました（" + fail + " 枚は失敗。Wi‑Fiでもう一度押すと続きから保存します）。" : "✓ 写真の保存が終わりました。電波がなくても見られます（地図は通信が必要）。");
    });
  }
  var sd = document.querySelector("[data-save-day]");
  if (sd) sd.addEventListener("click", function () { saveUrls(pageImages(), sd, null); });
  var sa = document.querySelector("[data-save-all]");
  if (sa) sa.addEventListener("click", function () {
    sa.disabled = true; say("ページを確認中…");
    var pages = ["index.html", "flights.html"]; for (var i = 1; i <= 13; i++) pages.push("day" + pad(i) + ".html");
    Promise.all(pages.map(function (p) { return fetch(p).then(function (r) { return r.text(); }); })).then(function (texts) {
      var urls = [];
      texts.forEach(function (tx) {
        var doc = new DOMParser().parseFromString(tx, "text/html");
        pageImages(doc).forEach(function (u) { if (urls.indexOf(u) < 0) urls.push(u); });
      });
      return saveUrls(urls, sa, document.querySelector("[data-offline-progress]"));
    }).catch(function () { sa.disabled = false; say("保存に失敗しました。通信を確認してもう一度。"); });
  });


  // ---------- 全ページ共通のメモ（緊急連絡先など）
  document.querySelectorAll("textarea[data-gmemo]").forEach(function (area) {
    var key = "techo:g:" + area.getAttribute("data-gmemo"), tm;
    area.value = store.get(key) || "";
    area.addEventListener("input", function () { clearTimeout(tm); tm = setTimeout(function () { store.set(key, area.value); }, 300); });
  });

  // ---------- お金：円換算とふたりの割り勘
  function readJSON(k, d) { try { return JSON.parse(store.get(k) || "") || d; } catch (e) { return d; } }
  function yen(n) { return Math.round(n).toLocaleString("ja-JP") + " 円"; }
  function eur(n) { return "€" + (Math.round(n * 100) / 100).toLocaleString("ja-JP", { minimumFractionDigits: 0, maximumFractionDigits: 2 }); }
  document.querySelectorAll("[data-money]").forEach(function (box) {
    var day = +box.getAttribute("data-day");
    var rateIn = box.querySelector("[data-fx-rate]"), eurIn = box.querySelector("[data-fx-eur]"), out = box.querySelector("[data-fx-yen]");
    var saved = store.get("techo:g:fx"); if (saved) rateIn.value = saved;
    function rate() { return parseFloat(rateIn.value) || 0; }
    function conv() { var v = parseFloat(eurIn.value); out.textContent = isNaN(v) ? "— 円" : yen(v * rate()); }
    eurIn.addEventListener("input", conv);
    rateIn.addEventListener("input", function () { store.set("techo:g:fx", rateIn.value); conv(); render(); });
    var names = readJSON("techo:g:names", { a: "", b: "" });
    box.querySelectorAll("[data-name]").forEach(function (inp) {
      var w = inp.getAttribute("data-name"); inp.value = names[w] || "";
      inp.addEventListener("input", function () { names[w] = inp.value.trim(); store.set("techo:g:names", JSON.stringify(names)); render(); });
    });
    function nm(w) { return names[w] || w.toUpperCase(); }
    var list = box.querySelector("[data-exp-list]"), sum = box.querySelector("[data-exp-sum]");
    function render() {
      box.querySelector("[data-name-a]").textContent = nm("a"); box.querySelector("[data-name-b]").textContent = nm("b");
      var all = readJSON("techo:g:expenses", []);
      var rows = day ? all.filter(function (x) { return x.day === day; }) : all;
      list.innerHTML = rows.map(function (x) {
        return '<li><span>' + (day ? "" : "DAY" + ("0" + x.day).slice(-2) + " ") + x.what.replace(/[<>&]/g, "") + '</span><b>' + eur(x.eur) + '</b><small>' + nm(x.who) + '</small><button type="button" data-del="' + x.id + '" aria-label="削除">×</button></li>';
      }).join("") || '<li class="empty">まだありません</li>';
      var ta = 0, tb = 0; rows.forEach(function (x) { if (x.who === "a") ta += x.eur; else tb += x.eur; });
      var total = ta + tb, diff = (ta - tb) / 2;
      sum.innerHTML = (day ? "この日" : "全日") + "の合計 <b>" + eur(total) + "</b>（約" + yen(total * rate()) + "）<br>" +
        nm("a") + " " + eur(ta) + "／" + nm("b") + " " + eur(tb) +
        (Math.abs(diff) >= 0.01 ? "<br>半分ずつにするなら：<b>" + (diff > 0 ? nm("b") + " → " + nm("a") : nm("a") + " → " + nm("b")) + " " + eur(Math.abs(diff)) + "（約" + yen(Math.abs(diff) * rate()) + "）</b>" : "");
    }
    box.querySelector("[data-exp-form]").addEventListener("submit", function (ev) {
      ev.preventDefault();
      var f = ev.target, v = parseFloat(f.eur.value);
      if (!f.what.value.trim() || isNaN(v)) return;
      var all = readJSON("techo:g:expenses", []);
      all.push({ id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6), day: day || 0, what: f.what.value.trim(), eur: v, who: f.who.value });
      store.set("techo:g:expenses", JSON.stringify(all));
      f.what.value = ""; f.eur.value = ""; render();
    });
    list.addEventListener("click", function (ev) {
      var b = ev.target.closest("[data-del]"); if (!b) return;
      var all = readJSON("techo:g:expenses", []).filter(function (x) { return x.id !== b.getAttribute("data-del"); });
      store.set("techo:g:expenses", JSON.stringify(all)); render();
    });
    render();
  });

  // ---------- ふたりで共有（リンクで送って取り込む）
  function allData() {
    var o = {};
    try { for (var i = 0; i < localStorage.length; i++) { var k = localStorage.key(i); if (k && k.indexOf("techo:") === 0) o[k] = localStorage.getItem(k); } } catch (e) {}
    return o;
  }
  function b64url(bytes) { var s = ""; bytes.forEach(function (b) { s += String.fromCharCode(b); }); return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, ""); }
  function unb64url(str) { var s = atob(str.replace(/-/g, "+").replace(/_/g, "/")); var a = new Uint8Array(s.length); for (var i = 0; i < s.length; i++) a[i] = s.charCodeAt(i); return a; }
  function pack(obj) {
    var bytes = new TextEncoder().encode(JSON.stringify(obj));
    if (window.CompressionStream) {
      var cs = new Blob([bytes]).stream().pipeThrough(new CompressionStream("deflate-raw"));
      return new Response(cs).arrayBuffer().then(function (buf) { return "z" + b64url(new Uint8Array(buf)); });
    }
    return Promise.resolve("p" + b64url(bytes));
  }
  function unpack(str) {
    var bytes = unb64url(str.slice(1));
    if (str[0] === "z") {
      var ds = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("deflate-raw"));
      return new Response(ds).text().then(JSON.parse);
    }
    return Promise.resolve(JSON.parse(new TextDecoder().decode(bytes)));
  }
  var mk = document.querySelector("[data-share-make]");
  if (mk) mk.addEventListener("click", function () {
    var data = allData(), n = Object.keys(data).length, st = document.querySelector("[data-share-state]"), ta = document.querySelector("[data-share-url]");
    if (!n) { st.textContent = "まだ共有する記録がありません。"; return; }
    pack(data).then(function (code) {
      var url = location.href.split("#")[0].replace(/[^/]*$/, "") + "index.html#share=" + code;
      ta.value = url; ta.hidden = false;
      st.textContent = n + "件の記録をリンクにしました（" + url.length + "文字）。";
      if (navigator.share) { navigator.share({ title: "ふたりの欧州手帖の記録", url: url }).catch(function () {}); }
      else if (navigator.clipboard) { navigator.clipboard.writeText(url).then(function () { st.textContent += " コピーしました。LINEなどに貼って送ってください。"; }); }
    });
  });
  function merge(incoming) {
    var res = { added: 0, merged: 0, kept: 0 };
    Object.keys(incoming).forEach(function (k) {
      if (k.indexOf("techo:") !== 0) return;
      var v = incoming[k], cur = store.get(k);
      if (cur === null || cur === "" || cur === "0" && v === "1") { store.set(k, v); res.added++; return; }
      if (cur === v) return;
      if (k === "techo:g:expenses") {
        var a = readJSON(k, []), ids = {}; a.forEach(function (x) { ids[x.id] = 1; });
        var b = []; try { b = JSON.parse(v); } catch (e) {}
        b.forEach(function (x) { if (!ids[x.id]) a.push(x); }); store.set(k, JSON.stringify(a)); res.merged++; return;
      }
      if (/:memo:|^techo:g:em-/.test(k)) {
        if (cur.indexOf(v) < 0 && v.indexOf(cur) < 0) { store.set(k, cur + "\n──（相手のメモ）──\n" + v); res.merged++; }
        else if (v.length > cur.length) { store.set(k, v); res.merged++; }
        return;
      }
      if (/^techo:hotel:/.test(k)) { try { if (!JSON.parse(cur).name) { store.set(k, v); res.added++; return; } } catch (e) {} }
      res.kept++;  // チェック（1/0）は付いている方、それ以外は自分の内容を残す
    });
    return res;
  }
  var idlg = document.getElementById("import-dlg"), pending = null;
  if (idlg) idlg.addEventListener("click", function (ev) {
    var b = ev.target.closest("[data-import]"); if (!b || !pending) return;
    if (b.getAttribute("data-import") === "ok") {
      var r = merge(pending);
      alertBox("取り込みました：新しく " + r.added + "件、合わせた " + r.merged + "件、自分の内容を残した " + r.kept + "件。");
      paintBooked(); labelHotels();
    }
    pending = null;
    if (idlg.close) idlg.close(); else idlg.removeAttribute("open");
    history.replaceState(null, "", location.pathname);
  });
  function checkImport() {
    var m = location.hash.match(/^#share=([A-Za-z0-9_-]+)$/);
    if (!m || !idlg) return;
    unpack(m[1]).then(function (data) {
      var keys = Object.keys(data).filter(function (k) { return k.indexOf("techo:") === 0; });
      idlg.querySelector("[data-import-summary]").textContent = keys.length + "件の記録（ホテル・予約済み・メモ・チェック・支出）を、この端末の記録と合わせます。この端末の内容は消えません。";
      pending = data;
      if (!idlg.open) { if (idlg.showModal) idlg.showModal(); else idlg.setAttribute("open", ""); }
    }).catch(function () { alertBox("共有リンクを読み取れませんでした。リンクが途中で切れていないか確認してください。"); });
  }
  checkImport();
  window.addEventListener("hashchange", checkImport);
  function alertBox(msg) {
    var st = document.querySelector("[data-share-state]");
    if (st) { st.textContent = msg; var p = document.getElementById("sec-share"); if (p) { p.open = true; p.scrollIntoView({ block: "start" }); } }
  }

  // 現在の日を帯の中で見える位置に
  var cur = document.querySelector('.days a[aria-current="page"]');
  if (cur && cur.scrollIntoView) cur.scrollIntoView({ block: "nearest", inline: "center" });
})();

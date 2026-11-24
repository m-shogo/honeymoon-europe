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

  // 現在の日を帯の中で見える位置に
  var cur = document.querySelector('.days a[aria-current="page"]');
  if (cur && cur.scrollIntoView) cur.scrollIntoView({ block: "nearest", inline: "center" });
})();

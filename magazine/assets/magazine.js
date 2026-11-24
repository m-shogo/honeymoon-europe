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
  // 現在の日を帯の中で見える位置に
  var cur = document.querySelector('.days a[aria-current="page"]');
  if (cur && cur.scrollIntoView) cur.scrollIntoView({ block: "nearest", inline: "center" });
})();

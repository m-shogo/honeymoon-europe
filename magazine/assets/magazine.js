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

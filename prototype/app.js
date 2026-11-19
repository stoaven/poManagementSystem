/* 货运订单费用管理 · 原型交互 */
(function () {
  "use strict";

  var login = document.getElementById("view-login");
  var app = document.getElementById("view-app");
  var modal = document.getElementById("modal-charge");

  var VIEWS = ["shipments", "shipment-detail", "options", "users"];
  var views = Array.prototype.slice.call(document.querySelectorAll(".view"));
  var railItems = Array.prototype.slice.call(document.querySelectorAll(".rail-item"));

  function current() {
    var h = (location.hash || "").replace(/^#\/?/, "").split("/")[0];
    return VIEWS.indexOf(h) >= 0 ? h : "shipments";
  }

  function wantsModal() {
    return (location.hash || "").indexOf("/modal") >= 0;
  }

  function show(name, push) {
    if (VIEWS.indexOf(name) < 0) { name = "shipments"; }
    views.forEach(function (v) {
      v.hidden = v.getAttribute("data-view") !== name;
    });
    railItems.forEach(function (b) {
      b.classList.toggle("is-active", b.getAttribute("data-go") === name);
    });
    if (push !== false && location.hash !== "#/" + name) {
      location.hash = "#/" + name;
    }
    window.scrollTo(0, 0);
  }

  function enterApp(name) {
    login.hidden = true;
    app.hidden = false;
    show(name || current());
  }

  /* ---------- hash 路由 ---------- */
  window.addEventListener("hashchange", function () {
    if (location.hash.indexOf("#/login") === 0) {
      app.hidden = true;
      login.hidden = false;
      return;
    }
    enterApp(current());
  });

  /* ---------- 登录 ---------- */
  document.getElementById("login-form").addEventListener("submit", function (e) {
    e.preventDefault();
    enterApp("shipments");
  });

  /* ---------- 事件委托 ---------- */
  document.addEventListener("click", function (e) {
    var rail = e.target.closest(".rail-item");
    if (rail) { show(rail.getAttribute("data-go")); return; }

    var row = e.target.closest(".row-link");
    if (row) { show("shipment-detail"); return; }

    var tab = e.target.closest(".tab");
    if (tab) {
      Array.prototype.forEach.call(tab.parentNode.children, function (t) {
        t.classList.toggle("is-on", t === tab);
      });
      return;
    }

    var sw = e.target.closest(".switch");
    if (sw) { sw.classList.toggle("is-on"); return; }

    if (e.target.closest('[data-action="new-charge"]')) {
      modal.hidden = false;
      return;
    }

    if (e.target.closest("[data-close]")) { modal.hidden = true; }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !modal.hidden) { modal.hidden = true; }
  });

  /* ---------- 选项名称省略时以代码呈现（与 spec「名称可省略」一致） ---------- */
  Array.prototype.forEach.call(document.querySelectorAll(".opt-name"), function (cell) {
    var row = cell.closest("tr");
    var code = row && row.querySelector(".opt-code");
    if (code) { cell.textContent = code.textContent; }
  });

  /* ---------- 从详情返回列表 ---------- */
  var back = document.createElement("button");
  back.className = "btn btn-ghost";
  back.textContent = "返回列表";
  back.addEventListener("click", function () { show("shipments"); });
  var actions = document.querySelector('[data-view="shipment-detail"] .page-actions');
  actions.insertBefore(back, actions.firstChild);

  /* ---------- 初始状态 ---------- */
  window.addEventListener("hashchange", function () {
    if (wantsModal()) { modal.hidden = false; }
  });
  if (location.hash.indexOf("#/login") === 0) {
    login.hidden = false;
    app.hidden = true;
  } else {
    var wantModal = wantsModal();
    enterApp(current());
    if (wantModal) { modal.hidden = false; }
  }
})();

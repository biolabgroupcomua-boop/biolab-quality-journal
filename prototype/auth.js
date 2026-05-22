// Перевірка авторизації + заповнення sidebar.
// Підключається на кожній сторінці окрім login.html.

(function checkAuth() {
  const raw = localStorage.getItem("current_user");
  let user = null;
  try { user = raw ? JSON.parse(raw) : null; } catch (e) { user = null; }
  if (!user || !user.role) {
    window.location.replace("login.html");
    return;
  }

  document.addEventListener("DOMContentLoaded", () => {
    const nameDiv = document.querySelector(".user-info .name");
    const roleDiv = document.querySelector(".user-info .role");
    if (nameDiv) nameDiv.textContent = user.name;
    if (roleDiv) roleDiv.textContent = user.role_label;

    // Додаємо кнопку "Вийти" один раз
    const userInfo = document.querySelector(".user-info");
    if (userInfo && !document.getElementById("logout-btn")) {
      const btn = document.createElement("button");
      btn.id = "logout-btn";
      btn.type = "button";
      btn.textContent = "Вийти";
      btn.style.cssText =
        "margin-top: 0.5rem; width: 100%; padding: 0.25rem 0.5rem; " +
        "font-size: 0.85em; background: transparent; " +
        "border: 1px solid rgba(255,255,255,0.3); color: white; " +
        "border-radius: 4px; cursor: pointer;";
      btn.addEventListener("mouseenter", () => {
        btn.style.background = "rgba(255,255,255,0.1)";
      });
      btn.addEventListener("mouseleave", () => {
        btn.style.background = "transparent";
      });
      btn.addEventListener("click", () => {
        localStorage.removeItem("current_user");
        window.location.replace("login.html");
      });
      userInfo.appendChild(btn);
    }
  });
})();

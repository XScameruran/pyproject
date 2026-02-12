const THEME_KEY = "theme";

const getStoredTheme = () => {
    const stored = window.localStorage.getItem(THEME_KEY);
    return stored === "dark" ? "dark" : "light";
};

const applyTheme = (theme) => {
    document.documentElement.setAttribute("data-theme", theme);
    const toggle = document.getElementById("theme-toggle");
    if (toggle) {
        toggle.textContent = theme === "light" ? "🌙" : "☀️";
    }
};

const toggleTheme = () => {
    const current = document.documentElement.getAttribute("data-theme") || "light";
    const next = current === "light" ? "dark" : "light";
    window.localStorage.setItem(THEME_KEY, next);
    applyTheme(next);
};

document.addEventListener("DOMContentLoaded", () => {
    const initialTheme = getStoredTheme();
    applyTheme(initialTheme);
    const toggle = document.getElementById("theme-toggle");
    if (toggle) {
        toggle.addEventListener("click", toggleTheme);
    }
});

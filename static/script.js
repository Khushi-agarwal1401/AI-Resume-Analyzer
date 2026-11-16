// DARK / LIGHT MODE TOGGLE
//
// The theme is stored as data-theme="dark" on the <html> element and the
// choice is saved in localStorage so it survives page reloads and works on
// both pages. This file is loaded in <head> so the saved theme is applied
// before the page is painted (no flash of the wrong theme).

const THEME_KEY = "resumeTheme";

function getSavedTheme() {
    try {
        return localStorage.getItem(THEME_KEY);
    } catch (error) {
        // Storage can be blocked (for example in private mode)
        return null;
    }
}

function saveTheme(theme) {
    try {
        localStorage.setItem(THEME_KEY, theme);
    } catch (error) {
        // The theme still switches, it just will not be remembered
    }
}

function applyTheme(theme) {
    if (theme === "dark") {
        document.documentElement.setAttribute("data-theme", "dark");
    } else {
        document.documentElement.removeAttribute("data-theme");
    }
}

// Used when the user clicks the toggle. Cards and buttons have a 0.3s CSS
// transition, which would leave some of them half-faded (light text on a
// light card) for a moment, so transitions are turned off during the switch.
function switchTheme(theme) {
    const root = document.documentElement;

    root.classList.add("theme-switching");
    applyTheme(theme);
    void root.offsetWidth; // force the browser to apply the new colors now
    root.classList.remove("theme-switching");
}

// Apply the saved theme immediately (light is the default)
applyTheme(getSavedTheme());

document.addEventListener("DOMContentLoaded", function () {

    const themeToggle = document.getElementById("themeToggle");

    if (!themeToggle) return;

    function isDark() {
        return document.documentElement.getAttribute("data-theme") === "dark";
    }

    function updateButton() {
        if (isDark()) {
            themeToggle.textContent = "☀️ Light Mode";
            themeToggle.setAttribute("aria-label", "Switch to light mode");
        } else {
            themeToggle.textContent = "🌙 Dark Mode";
            themeToggle.setAttribute("aria-label", "Switch to dark mode");
        }
    }

    updateButton();

    themeToggle.addEventListener("click", function () {

        const newTheme = isDark() ? "light" : "dark";

        switchTheme(newTheme);
        saveTheme(newTheme);
        updateButton();
    });

});
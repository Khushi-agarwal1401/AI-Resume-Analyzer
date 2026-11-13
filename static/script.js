
// DARK / LIGHT MODE TOGGLE

document.addEventListener("DOMContentLoaded", function () {

    const themeToggle = document.getElementById("themeToggle");

    // Load previously saved theme
    const savedTheme = localStorage.getItem("resumeTheme");

    if (savedTheme === "dark") {
        document.body.classList.add("dark-mode");
    }

    function updateButton() {
        if (!themeToggle) return;

        if (document.body.classList.contains("dark-mode")) {
            themeToggle.textContent = "☀️ Light Mode";
        } else {
            themeToggle.textContent = "🌙 Dark Mode";
        }
    }

    updateButton();

    if (themeToggle) {
        themeToggle.addEventListener("click", function () {

            document.body.classList.toggle("dark-mode");

            const currentTheme =
                document.body.classList.contains("dark-mode")
                    ? "dark"
                    : "light";

            localStorage.setItem("resumeTheme", currentTheme);

            updateButton();
        });
    }

});


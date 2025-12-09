/* ========== DARK / LIGHT MODE ========== */
const themeBtn = document.getElementById("themeToggle");

themeBtn.addEventListener("click", () => {
    document.body.classList.toggle("dark");

    if (document.body.classList.contains("dark")) {
        themeBtn.textContent = "☀️ Light Mode";
    } else {
        themeBtn.textContent = "🌙 Dark Mode";
    }
});


/* ========== SUBMIT SETTINGS ========== */
document.getElementById("settingsForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    let sensitivity = document.getElementById("sensitivity").value;
    let logEnabled = document.getElementById("logEnabled").value;

    let res = await fetch("/update-settings", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: `sensitivity=${sensitivity}&log_enabled=${logEnabled}`
    });

    let result = await res.json();

    // UI Feedback
    let statusText = document.getElementById("statusText");
    if (result.status === "success") {
        statusText.innerHTML = "✔ Lưu cấu hình thành công!";
        statusText.style.color = "#4CAF50";
    } else {
        statusText.innerHTML = "❌ Có lỗi xảy ra!";
        statusText.style.color = "red";
    }
});

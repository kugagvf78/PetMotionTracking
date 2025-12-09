/* ==========================================
   DARK MODE
========================================== */
const themeBtn = document.getElementById("themeToggle");
const themeIcon = document.getElementById("themeIcon");
const themeText = document.getElementById("themeText");

// Load saved theme
if (localStorage.getItem("theme") === "dark") {
    document.body.classList.add("dark");
    themeIcon.textContent = "☀️";
    themeText.textContent = "Light Mode";
}

themeBtn.addEventListener("click", () => {
    document.body.classList.toggle("dark");

    const dark = document.body.classList.contains("dark");
    themeIcon.textContent = dark ? "☀️" : "🌙";
    themeText.textContent = dark ? "Light Mode" : "Dark Mode";

    localStorage.setItem("theme", dark ? "dark" : "light");
});

/* ==========================================
   CHART
========================================== */
const ctx = document.getElementById("motionChart").getContext("2d");

let chart = new Chart(ctx, {
    type: "line",
    data: { labels: [], datasets: [{
        label: "Chuyển động",
        data: [],
        borderColor: "#22c55e",
        backgroundColor: "rgba(34,197,94,0.15)",
        tension: 0.3,
        fill: true,
        borderWidth: 2
    }]},
    options: {
        responsive: true,
        scales: { y: { beginAtZero: true } }
    }
});

/* ==========================================
   FETCH MOTION STATS
========================================== */
function updateChart() {
    fetch("/motion_stats")
        .then(res => res.json())
        .then(data => {
            chart.data.labels = data.map(d => d.time);
            chart.data.datasets[0].data = data.map(d => d.count);
            chart.update();
        });
}

/* ==========================================
   LOAD LOG ENTRIES
========================================== */
function loadLogs() {
    fetch("/get_logs")
        .then(res => res.json())
        .then(logs => {
            const logList = document.getElementById("logList");
            logList.innerHTML = "";

            logs.forEach((entry) => {
                const div = document.createElement("div");
                div.className = "log-item";

                const [time, msg] = entry.split(" - ");

                div.innerHTML = `
                    <span class="log-time">⏱ ${time}</span>
                    <span>${msg}</span>
                `;

                logList.appendChild(div);
            });

            // 🔥 FIXED: LẤY LOG MỚI NHẤT (DÒNG CUỐI)
            if (logs.length > 0) {
                const latestLog = logs[logs.length - 1];
                const [latestTime] = latestLog.split(" - ");
                document.getElementById("lastTime").textContent = latestTime;
            }

            document.getElementById("totalEvents").textContent = logs.length;
            document.getElementById("todayCount").textContent = logs.length;
        });
}

/* ==========================================
   REALTIME ALERT SYSTEM
========================================== */
function pushAlert(text) {
    const panel = document.getElementById("alertPanel");

    const alert = document.createElement("div");
    alert.className = "alert-box";
    alert.textContent = text;

    panel.prepend(alert);

    if (panel.children.length > 10) {
        panel.removeChild(panel.lastChild);
    }
}

/* ==========================================
   LOAD SENSOR STATUS (PIR + RFID + AI)
========================================== */
function loadSensors() {
    fetch("/sensor_status")
        .then(res => res.json())
        .then(data => {
            document.getElementById("pirStatus").textContent = data.pir ? "Kích hoạt" : "Không hoạt động";
            document.getElementById("rfidStatus").textContent = data.rfid || "---";

            if (data.pir) pushAlert("📡 PIR phát hiện chuyển động!");
            if (data.rfid) pushAlert("🐾 RFID phát hiện thú cưng!");

            if (data.pet_detected) {
                document.getElementById("petStatus").textContent = "Phát hiện 🐶";
                pushAlert("🐶 Pet AI: Đã nhận diện thú cưng!");
            } else {
                document.getElementById("petStatus").textContent = "Không thấy";
            }

            document.getElementById("behaviorScore").textContent = data.behavior_score;
        });
}

/* ==========================================
   CAMERA STATUS
========================================== */
function checkCamera() {
    fetch("/camera_status")
        .then(res => res.json())
        .then(data => {
            const cam = document.getElementById("cameraStatus");
            cam.textContent = data.active ? "Hoạt động" : "Không hoạt động";
            cam.style.color = data.active ? "#22c55e" : "var(--danger)";
        });
}

/* ==========================================
   AUTO REFRESH LOOP
========================================== */
function refreshAll() {
    updateChart();
    loadLogs();
    checkCamera();
    loadSensors();
}

setInterval(refreshAll, 2500);
refreshAll();

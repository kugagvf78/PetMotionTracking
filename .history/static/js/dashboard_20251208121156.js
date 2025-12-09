/* ===== DARK MODE ===== */
const themeBtn = document.getElementById("themeToggle");

if (localStorage.getItem("theme") === "dark") {
    document.body.classList.add("dark");
    themeBtn.textContent = "☀️ Light Mode";
}

themeBtn.addEventListener("click", () => {
    document.body.classList.toggle("dark");
    const dark = document.body.classList.contains("dark");

    themeBtn.textContent = dark ? "☀️ Light Mode" : "🌙 Dark Mode";
    localStorage.setItem("theme", dark ? "dark" : "light");
});

/* ===== CHART SETUP ===== */
const ctx = document.getElementById("motionChart").getContext("2d");

let chart = new Chart(ctx, {
    type: "line",
    data: {
        labels: [],
        datasets: [{
            label: "Số lần chuyển động",
            data: [],
            borderColor: "#4CAF50",
            backgroundColor: "rgba(76,175,80,0.15)",
            borderWidth: 2,
            tension: 0.35,
            fill: true
        }]
    },
    options: {
        responsive: true,
        scales: {
            y: { beginAtZero: true }
        }
    }
});

/* ===== UPDATE CHART ===== */
function updateChart() {
    fetch("/motion_stats")
        .then(res => res.json())
        .then(data => {
            chart.data.labels = data.map(x => x.time);
            chart.data.datasets[0].data = data.map(x => x.count);
            chart.update();

            if (data.length > 0) {
                const peak = data.reduce((a, b) => a.count > b.count ? a : b);
                document.getElementById("peakTime").textContent = peak.time;
            }
        });
}

/* ===== LOAD LOGS ===== */
function loadLogs() {
    fetch("/get_logs")
        .then(res => res.json())
        .then(logs => {
            const logList = document.getElementById("logList");
            logList.innerHTML = "";

            if (logs.length === 0) {
                logList.innerHTML = `<div class="no-logs">Chưa có hoạt động</div>`;
                return;
            }

            document.getElementById("totalEvents").textContent = logs.length;
            document.getElementById("todayCount").textContent = logs.length;

            logs.slice(0, 20).forEach((line, i) => {
                const div = document.createElement("div");
                div.className = "log-item";

                if (line.includes(" - ")) {
                    const [time, msg] = line.split(" - ");
                    div.innerHTML = `<span class="log-time">${time}</span>${msg}`;

                    if (i === 0) {
                        document.getElementById("lastTime").textContent = time;
                    }
                }

                logList.appendChild(div);
            });
        });
}

/* ===== CAMERA STATUS ===== */
function checkCamera() {
    fetch("/camera_status")
        .then(res => res.json())
        .then(data => {
            let cam = document.getElementById("cameraStatus");
            cam.textContent = (data.status === "active" && data.has_frame)
                ? "Hoạt động"
                : "Không hoạt động";

            cam.style.color = cam.textContent === "Hoạt động" ? "#22c55e" : "#ef4444";
        });
}

/* ===== AUTOMATIC REFRESH ===== */
function refreshAll() {
    updateChart();
    loadLogs();
    checkCamera();
}

setInterval(refreshAll, 3000);
refreshAll();

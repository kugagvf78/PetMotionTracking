/* ========== DARK MODE ========== */
const themeBtn = document.getElementById("themeToggle");

// Load theme từ localStorage
if (localStorage.getItem("theme") === "dark") {
    document.body.classList.add("dark");
    themeBtn.textContent = "☀️ Light Mode";
}

themeBtn.addEventListener("click", () => {
    document.body.classList.toggle("dark");

    if (document.body.classList.contains("dark")) {
        themeBtn.textContent = "☀️ Light Mode";
        localStorage.setItem("theme", "dark");
    } else {
        themeBtn.textContent = "🌙 Dark Mode";
        localStorage.setItem("theme", "light");
    }
});

/* ========== CHART ========== */
const ctx = document.getElementById("motionChart").getContext("2d");
let chart = new Chart(ctx, {
    type: "line",
    data: {
        labels: [],
        datasets: [{
            label: "Số lần chuyển động",
            data: [],
            borderColor: "#22c55e",
            backgroundColor: "rgba(34,197,94,0.1)",
            borderWidth: 2,
            fill: true,
            tension: 0.4
        }]
    },
    options: {
        scales: {
            y: { beginAtZero: true }
        }
    }
});

/* ========== UPDATE CHART ========== */
function updateChart() {
    fetch("/motion_stats")
        .then(res => res.json())
        .then(data => {
            chart.data.labels = data.map(d => d.time);
            chart.data.datasets[0].data = data.map(d => d.count);
            chart.update();

            if (data.length > 0) {
                const peak = data.reduce((a, b) => a.count > b.count ? a : b);
                document.getElementById("peakTime").textContent = peak.time;
            }
        });
}

/* ========== LOAD LOGS ========== */
function loadLogs() {
    fetch("/get_logs")
        .then(res => res.json())
        .then(logs => {
            const logList = document.getElementById("logList");
            logList.innerHTML = "";

            if (logs.length === 0) {
                logList.innerHTML = `<div class="no-logs"><p>🔍 Chưa có hoạt động</p></div>`;
                return;
            }

            document.getElementById("totalEvents").textContent = logs.length;
            document.getElementById("todayCount").textContent = logs.length;

            logs.slice(0, 20).forEach((item, i) => {
                const div = document.createElement("div");
                div.className = "log-item";

                if (item.includes(" - ")) {
                    const [time, msg] = item.split(" - ");
                    div.innerHTML = `<span class='log-time'>⏱️ ${time}</span> ${msg}`;

                    if (i === 0) document.getElementById("lastTime").textContent = time;
                }

                logList.appendChild(div);
            });
        });
}

/* ========== CAMERA STATUS ========== */
function checkCamera() {
    fetch("/camera_status")
        .then(res => res.json())
        .then(data => {
            const status = document.getElementById("cameraStatus");
            if (data.status === "active" && data.has_frame) {
                status.textContent = "Hoạt động";
                status.style.color = "#22c55e";
            } else {
                status.textContent = "Không hoạt động";
                status.style.color = "#ef4444";
            }
        });
}

/* ========== REFRESH AUTOMATICALLY ========== */
function refreshAll() {
    updateChart();
    loadLogs();
    checkCamera();
}

setInterval(refreshAll, 3000);
refreshAll();

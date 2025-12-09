/* ===============================
    DARK / LIGHT MODE SWITCH
================================= */
const themeBtn = document.getElementById("themeToggle");

themeBtn.addEventListener("click", () => {
    document.body.classList.toggle("dark");

    if (document.body.classList.contains("dark")) {
        themeBtn.textContent = "☀️ Light Mode";
    } else {
        themeBtn.textContent = "🌙 Dark Mode";
    }
});

/* ===============================
    LOAD MOTION LOGS (AJAX)
================================= */
async function loadLogs() {
    let res = await fetch("/get_logs");
    let logs = await res.json();

    let logList = document.getElementById("logList");
    logList.innerHTML = "";

    logs.forEach(item => {
        const [time, message] = item.split(" - ");

        let div = document.createElement("div");
        div.className = "log-item";
        div.innerHTML = `
            <span class="time">${time}</span> — 
            <span>${message}</span>
        `;

        logList.appendChild(div);
    });

    updateChart(logs);
}

// refresh logs every 2 seconds
setInterval(loadLogs, 2000);
loadLogs();


/* ===============================
        CHART.JS — BIỂU ĐỒ
================================= */
let ctx = document.getElementById("motionChart").getContext("2d");

let motionChart = new Chart(ctx, {
    type: "line",
    data: {
        labels: [],
        datasets: [{
            label: "Motion Count",
            data: [],
            borderColor: "#4CAF50",
            borderWidth: 3,
            fill: false,
            tension: 0.3
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: { display: false }
        },
        scales: {
            x: { ticks: { color: "var(--text)" } },
            y: { ticks: { color: "var(--text)" } }
        }
    }
});


function updateChart(logs) {
    let hourMap = {};

    logs.forEach(item => {
        let time = item.split(" - ")[0];
        let hour = time.split(" ")[1].split(":")[0];

        hourMap[hour] = (hourMap[hour] || 0) + 1;
    });

    motionChart.data.labels = Object.keys(hourMap);
    motionChart.data.datasets[0].data = Object.values(hourMap);

    motionChart.update();
}

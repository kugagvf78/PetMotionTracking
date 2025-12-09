// ==============================
// LOAD LOGS + UPDATE CHART REALTIME
// ==============================

let chart = null;

function initChart() {
    const ctx = document.getElementById("motionChart").getContext("2d");

    chart = new Chart(ctx, {
        type: "line",
        data: {
            labels: [],            // thời gian
            datasets: [{
                label: "Số lần chuyển động",
                data: [],
                borderColor: "rgb(75, 192, 192)",
                borderWidth: 2,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

// Hàm tính tần suất từ file logs
function calculateFrequency(logs) {
    let count = {};

    logs.forEach(line => {
        let time = line.split(" - ")[0];   // "HH:MM:SS"
        let hour = time.substring(0, 2);  // lấy giờ

        count[hour] = (count[hour] || 0) + 1;
    });

    return count;
}

function updateChart() {
    fetch("/get_logs")
        .then(res => res.json())
        .then(logs => {
            let freq = calculateFrequency(logs);

            chart.data.labels = Object.keys(freq);
            chart.data.datasets[0].data = Object.values(freq);
            chart.update();
        });
}

// ==============================
// LOAD LOG LIST
// ==============================
function loadLogs() {
    fetch("/get_logs")
        .then(res => res.json())
        .then(logs => {
            let logList = document.getElementById("logList");
            logList.innerHTML = "";

            logs.forEach(item => {
                let div = document.createElement("div");
                div.className = "log-item";
                div.innerText = item;
                logList.appendChild(div);
            });
        });
}

// ==============================
// AUTO REFRESH mỗi 2 giây
// ==============================
setInterval(() => {
    updateChart();
    loadLogs();
}, 2000);

// Khởi tạo biểu đồ khi trang load
window.onload = () => {
    initChart();
    loadLogs();
    updateChart();
};

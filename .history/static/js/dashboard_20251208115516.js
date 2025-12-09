// =====================
//    BIỂU ĐỒ
// =====================
const ctx = document.getElementById("motionChart").getContext("2d");

let chart = new Chart(ctx, {
    type: "line",
    data: {
        labels: [],
        datasets: [{
            label: "Số lần chuyển động",
            data: [],
            borderColor: "#00bcd4",
            borderWidth: 3,
            fill: false,
            tension: 0.3
        }]
    },
    options: {
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});

// =====================
//  HÀM TẢI DỮ LIỆU CHO CHART
// =====================
function updateChart() {
    fetch("/motion_stats")
        .then(res => res.json())
        .then(data => {
            const labels = data.map(item => item.hour);
            const counts = data.map(item => item.count);

            chart.data.labels = labels;
            chart.data.datasets[0].data = counts;

            chart.update();
        })
        .catch(err => console.log("Chart update error:", err));
}

// Cập nhật biểu đồ mỗi 2 giây
setInterval(updateChart, 2000);

// Load lần đầu
updateChart();



// =====================
// TẢI LOG REALTIME
// =====================
function loadLogs() {
    fetch("/get_logs")
        .then(res => res.json())
        .then(logs => {
            const logList = document.getElementById("logList");
            logList.innerHTML = "";

            logs.forEach(item => {
                const div = document.createElement("div");
                div.className = "log-item";
                div.innerText = item;
                logList.appendChild(div);
            });
        });
}

setInterval(loadLogs, 2000);
loadLogs();

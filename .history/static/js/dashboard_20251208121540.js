// ===== THEME TOGGLE =====
        const themeBtn = document.getElementById("themeToggle");
        const themeIcon = document.getElementById("themeIcon");
        const themeText = document.getElementById("themeText");

        if (localStorage.getItem("theme") === "dark") {
            document.body.classList.add("dark");
            themeIcon.textContent = "☀️";
            themeText.textContent = "Light Mode";
        }

        themeBtn.addEventListener("click", () => {
            document.body.classList.toggle("dark");
            const isDark = document.body.classList.contains("dark");
            
            themeIcon.textContent = isDark ? "☀️" : "🌙";
            themeText.textContent = isDark ? "Light Mode" : "Dark Mode";
            localStorage.setItem("theme", isDark ? "dark" : "light");

            // Update chart colors on theme change
            updateChartTheme(isDark);
        });

        // ===== CHART SETUP =====
        const ctx = document.getElementById("motionChart").getContext("2d");
        const isDarkMode = document.body.classList.contains("dark");

        let chart = new Chart(ctx, {
            type: "line",
            data: {
                labels: [],
                datasets: [{
                    label: "Số lần phát hiện",
                    data: [],
                    borderColor: "#10b981",
                    backgroundColor: "rgba(16, 185, 129, 0.1)",
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5,
                    pointBackgroundColor: "#10b981",
                    pointBorderColor: isDarkMode ? "#18181b" : "#ffffff",
                    pointBorderWidth: 2,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: isDarkMode ? "#27272a" : "#ffffff",
                        titleColor: isDarkMode ? "#f8fafc" : "#0f172a",
                        bodyColor: isDarkMode ? "#94a3b8" : "#64748b",
                        borderColor: isDarkMode ? "#3f3f46" : "#e2e8f0",
                        borderWidth: 1,
                        padding: 12,
                        displayColors: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { 
                            color: isDarkMode ? "#94a3b8" : "#64748b",
                            stepSize: 1,
                            font: { size: 12 }
                        },
                        grid: {
                            color: isDarkMode ? "#27272a" : "#e2e8f0",
                            drawBorder: false
                        }
                    },
                    x: {
                        ticks: { 
                            color: isDarkMode ? "#94a3b8" : "#64748b",
                            font: { size: 11 }
                        },
                        grid: {
                            color: isDarkMode ? "#27272a" : "#e2e8f0",
                            drawBorder: false
                        }
                    }
                }
            }
        });

        function updateChartTheme(isDark) {
            chart.options.plugins.tooltip.backgroundColor = isDark ? "#27272a" : "#ffffff";
            chart.options.plugins.tooltip.titleColor = isDark ? "#f8fafc" : "#0f172a";
            chart.options.plugins.tooltip.bodyColor = isDark ? "#94a3b8" : "#64748b";
            chart.options.plugins.tooltip.borderColor = isDark ? "#3f3f46" : "#e2e8f0";
            chart.options.scales.y.ticks.color = isDark ? "#94a3b8" : "#64748b";
            chart.options.scales.x.ticks.color = isDark ? "#94a3b8" : "#64748b";
            chart.options.scales.y.grid.color = isDark ? "#27272a" : "#e2e8f0";
            chart.options.scales.x.grid.color = isDark ? "#27272a" : "#e2e8f0";
            chart.data.datasets[0].pointBorderColor = isDark ? "#18181b" : "#ffffff";
            chart.update();
        }

        // ===== UPDATE CHART =====
        function updateChart() {
            fetch("/motion_stats")
                .then(res => res.json())
                .then(data => {
                    chart.data.labels = data.map(x => x.time);
                    chart.data.datasets[0].data = data.map(x => x.count);
                    chart.update();

                    if (data.length > 0) {
                        const peak = data.reduce((max, curr) => curr.count > max.count ? curr : max, data[0]);
                        document.getElementById("peakTime").textContent = peak.time;
                    }
                })
                .catch(err => console.error("Chart update error:", err));
        }

        // ===== LOAD LOGS =====
        function loadLogs() {
            fetch("/get_logs")
                .then(res => res.json())
                .then(logs => {
                    const logList = document.getElementById("logList");
                    
                    if (logs.length === 0) {
                        logList.innerHTML = '<div class="no-logs"><p>🔍 Chưa ghi nhận chuyển động nào</p><small>Hệ thống sẽ tự động ghi lại khi phát hiện thú cưng di chuyển</small></div>';
                        return;
                    }

                    logList.innerHTML = "";
                    
                    document.getElementById("totalEvents").textContent = logs.length;
                    document.getElementById("todayCount").textContent = logs.length;

                    logs.slice(0, 25).forEach((item, index) => {
                        const div = document.createElement("div");
                        div.className = "log-item";
                        
                        if (item.includes(" - ")) {
                            const parts = item.split(" - ");
                            const time = parts[0].trim();
                            const message = parts.slice(1).join(" - ");
                            div.innerHTML = `<span class="log-time">⏱️ ${time}</span><span class="log-message">${message}</span>`;
                            
                            if (index === 0) {
                                document.getElementById("lastTime").textContent = time;
                            }
                        } else {
                            div.innerHTML = `<span class="log-message">${item}</span>`;
                        }
                        
                        logList.appendChild(div);
                    });
                })
                .catch(err => console.error("Logs load error:", err));
        }

        // ===== CHECK CAMERA =====
        function checkCamera() {
            fetch("/camera_status")
                .then(res => res.json())
                .then(data => {
                    const status = document.getElementById("cameraStatus");
                    if (data.status === "active" && data.has_frame) {
                        status.textContent = "Hoạt động";
                        status.style.color = "#10b981";
                    } else {
                        status.textContent = "Không hoạt động";
                        status.style.color = "#ef4444";
                    }
                })
                .catch(() => {
                    document.getElementById("cameraStatus").textContent = "Lỗi kết nối";
                    document.getElementById("cameraStatus").style.color = "#f59e0b";
                });
        }

        // ===== AUTO REFRESH =====
        function refreshAll() {
            updateChart();
            loadLogs();
            checkCamera();
        }

        setInterval(refreshAll, 3000);
        refreshAll();
// =====================
      // CHART SETUP
      // =====================
      const ctx = document.getElementById("motionChart").getContext("2d");
      let chart = new Chart(ctx, {
        type: "line",
        data: {
          labels: [],
          datasets: [
            {
              label: "Số lần chuyển động",
              data: [],
              borderColor: "#22c55e",
              backgroundColor: "rgba(34, 197, 94, 0.1)",
              borderWidth: 2,
              fill: true,
              tension: 0.4,
              pointRadius: 4,
              pointBackgroundColor: "#22c55e",
              pointBorderColor: "#18181b",
              pointBorderWidth: 2,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          plugins: {
            legend: {
              display: false,
            },
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: {
                color: "#a1a1aa",
                stepSize: 1,
              },
              grid: {
                color: "#27272a",
              },
            },
            x: {
              ticks: { color: "#a1a1aa" },
              grid: {
                color: "#27272a",
              },
            },
          },
        },
      });

      // =====================
      // UPDATE CHART
      // =====================
      function updateChart() {
        fetch("/motion_stats")
          .then((res) => res.json())
          .then((data) => {
            chart.data.labels = data.map((x) => x.time);
            chart.data.datasets[0].data = data.map((x) => x.count);
            chart.update();

            // Update peak time
            if (data.length > 0) {
              const peak = data.reduce(
                (max, curr) => (curr.count > max.count ? curr : max),
                data[0]
              );
              document.getElementById("peakTime").textContent = peak.time;
            }
          });
      }

      // =====================
      // LOAD LOGS
      // =====================
      function loadLogs() {
        fetch("/get_logs")
          .then((res) => res.json())
          .then((logs) => {
            const logList = document.getElementById("logList");

            if (logs.length === 0) {
              logList.innerHTML =
                '<div class="no-logs"><p>🔍 Chưa có hoạt động nào được ghi nhận</p></div>';
              return;
            }

            logList.innerHTML = "";

            // Update stats
            document.getElementById("totalEvents").textContent = logs.length;
            document.getElementById("todayCount").textContent = logs.length;

            // Show latest logs (max 20)
            logs.slice(0, 20).forEach((item) => {
              const div = document.createElement("div");
              div.className = "log-item";

              if (item.includes(" - ")) {
                const [time, message] = item.split(" - ", 2);
                div.innerHTML = `<span class="log-time">⏱️ ${time}</span><span class="log-message">${message}</span>`;

                // Update last time
                if (logs.indexOf(item) === 0) {
                  document.getElementById("lastTime").textContent = time
                    .trim()
                    .split(" ")
                    .pop();
                }
              } else {
                div.innerHTML = `<span class="log-message">${item}</span>`;
              }

              logList.appendChild(div);
            });
          });
      }

      // =====================
      // CHECK CAMERA STATUS
      // =====================
      function checkCamera() {
        fetch("/camera_status")
          .then((res) => res.json())
          .then((data) => {
            const status = document.getElementById("cameraStatus");
            if (data.status === "active" && data.has_frame) {
              status.textContent = "Hoạt động";
              status.style.color = "#22c55e";
            } else {
              status.textContent = "Không hoạt động";
              status.style.color = "#ef4444";
            }
          })
          .catch(() => {
            document.getElementById("cameraStatus").textContent = "Lỗi";
          });
      }

      // =====================
      // AUTO REFRESH
      // =====================
      function refreshAll() {
        updateChart();
        loadLogs();
        checkCamera();
      }

      // Refresh button
      document
        .getElementById("refreshBtn")
        .addEventListener("click", refreshAll);

      // Auto refresh every 3 seconds
      setInterval(refreshAll, 3000);

      // Initial load
      refreshAll();

      
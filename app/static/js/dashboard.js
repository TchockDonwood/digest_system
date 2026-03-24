const API_BASE = "http://localhost:8000/admin/stats";

// Храним графики, чтобы не дублировать
let charts = {};

// 🔹 Получение данных
async function fetchData(url) {
    const res = await fetch(url);
    return await res.json();
}

// 🔹 Подготовка данных
function prepareChartData(data, field = "value") {
    return {
        labels: data.map(item => new Date(item.period).toLocaleString()),
        values: data.map(item => item[field])
    };
}

// 🔹 Рендер графика
function renderChart(canvasId, label, data) {
    const ctx = document.getElementById(canvasId);

    // если уже есть график → уничтожаем
    if (charts[canvasId]) {
        charts[canvasId].destroy();
    }

    charts[canvasId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: label,
                data: data.values,
                borderWidth: 2
            }]
        }
    });
}

// 🔥 Основная функция загрузки
async function loadData() {
    const dateFrom = document.getElementById("dateFrom").value;
    const dateTo = document.getElementById("dateTo").value;

    if (!dateFrom || !dateTo) {
        alert("Выбери даты");
        return;
    }

    const fromISO = new Date(dateFrom).toISOString();
    const toISO = new Date(dateTo).toISOString();

    // 📈 Activity
    const activity = await fetchData(
        `${API_BASE}/activity/${fromISO}/${toISO}?group_by=day`
    );

    renderChart(
        "activityChart",
        "Requests",
        prepareChartData(activity)
    );

    // 👤 Registrations
    const registrations = await fetchData(
        `${API_BASE}/registrations/${fromISO}/${toISO}?group_by=day`
    );

    renderChart(
        "registrationsChart",
        "Registrations",
        prepareChartData(registrations)
    );

    // ⚙️ Metrics
    const metrics = await fetchData(
        `${API_BASE}/metrics/${fromISO}/${toISO}?group_by=day`
    );

    renderChart(
        "metricsRequests",
        "Total Requests",
        prepareChartData(metrics, "total_requests")
    );

    renderChart(
        "metricsLatency",
        "Avg Response Time",
        prepareChartData(metrics, "avg_response_time")
    );
}

(function () {
    function renderPriceChart(chartCanvas) {
        const labels = JSON.parse(chartCanvas.dataset.labels);
        const values = JSON.parse(chartCanvas.dataset.values);
        const selectedInterval = chartCanvas.dataset.interval;
        const chartInfo = chartCanvas.parentElement.querySelector(".chart-info");
        const context = chartCanvas.getContext("2d");
        const minValue = Math.min(...values);
        const maxValue = Math.max(...values);
        const valueRange = maxValue - minValue || 1;
        let width = chartCanvas.width;
        let height = chartCanvas.height;
        let horizontalPadding = 48;
        let topPadding = 48;
        let bottomPadding = 24;
        let fontSize = 12;
        let xStep = 1;
        let selectedIndex = null;

        function resizeChart() {
            const pixelRatio = window.devicePixelRatio || 1;
            const isMobile = window.matchMedia("(max-width: 700px)").matches;
            const panelStyle = window.getComputedStyle(chartCanvas.parentElement);
            const panelHorizontalPadding = parseFloat(panelStyle.paddingLeft) + parseFloat(panelStyle.paddingRight);
            const chartWidth = chartCanvas.parentElement.clientWidth - panelHorizontalPadding - 2;

            width = Math.max(chartWidth, 280);
            height = isMobile ? 280 : 320;
            horizontalPadding = isMobile ? 76 : 58;
            topPadding = isMobile ? 42 : 40;
            bottomPadding = 18;
            fontSize = isMobile ? 15 : 12;
            xStep = (width - horizontalPadding * 2) / Math.max(labels.length - 1, 1);

            chartCanvas.style.width = `${width}px`;
            chartCanvas.style.height = `${height}px`;
            chartCanvas.width = Math.floor(width * pixelRatio);
            chartCanvas.height = Math.floor(height * pixelRatio);

            context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
        }

        function getPoint(index) {
            const x = horizontalPadding + xStep * index;
            const value = values[index];
            const chartHeight = height - topPadding - bottomPadding;
            const y = height - bottomPadding - ((value - minValue) / valueRange) * chartHeight;

            return { x, y, value };
        }

        function drawChart(selectedIndex = null) {
            context.clearRect(0, 0, width, height);
            context.font = `${fontSize}px Arial`;
            context.strokeStyle = "#d9e2ec";
            context.lineWidth = 1;

            for (let i = 0; i <= 4; i += 1) {
                const y = topPadding + ((height - topPadding - bottomPadding) / 4) * i;
                context.beginPath();
                context.moveTo(horizontalPadding, y);
                context.lineTo(width - horizontalPadding, y);
                context.stroke();
            }

            context.strokeStyle = "#0b5cad";
            context.lineWidth = 3;
            context.beginPath();

            values.forEach((value, index) => {
                const point = getPoint(index);

                if (index === 0) {
                    context.moveTo(point.x, point.y);
                } else {
                    context.lineTo(point.x, point.y);
                }
            });

            context.stroke();

            context.fillStyle = "#0b5cad";
            values.forEach((value, index) => {
                const point = getPoint(index);

                context.beginPath();
                context.arc(point.x, point.y, 4, 0, Math.PI * 2);
                context.fill();
            });

            if (selectedIndex !== null) {
                const point = getPoint(selectedIndex);

                context.strokeStyle = "#b42318";
                context.lineWidth = 2;
                context.beginPath();
                context.moveTo(point.x, topPadding);
                context.lineTo(point.x, height - bottomPadding);
                context.stroke();

                context.fillStyle = "#b42318";
                context.beginPath();
                context.arc(point.x, point.y, 6, 0, Math.PI * 2);
                context.fill();
            }

            context.fillStyle = "#52606d";
            context.fillText(maxValue.toFixed(2), 8, topPadding + 4);
            context.fillText(minValue.toFixed(2), 8, height - bottomPadding + 4);
        }

        resizeChart();
        drawChart();

        chartCanvas.addEventListener("click", (event) => {
            const rect = chartCanvas.getBoundingClientRect();
            const clickX = event.clientX - rect.left;
            const rawIndex = Math.round((clickX - horizontalPadding) / xStep);
            selectedIndex = Math.max(0, Math.min(values.length - 1, rawIndex));

            drawChart(selectedIndex);

            if (chartInfo) {
                const label = ["recorded", "hourly"].includes(selectedInterval) ? "Time" : "Period";
                const valueLabel = chartCanvas.dataset.valueLabel
                    || (selectedInterval === "recorded" ? "Price" : "Average price");

                chartInfo.textContent = `${label}: ${labels[selectedIndex]} | ${valueLabel}: ${values[selectedIndex].toFixed(2)}`;
            }
        });

        window.addEventListener("resize", () => {
            resizeChart();
            drawChart(selectedIndex);
        });
    }

    document.querySelectorAll(".price-chart").forEach(renderPriceChart);
}());

(function () {
    function sortValue(cell) {
        if (!cell) {
            return null;
        }

        const raw = cell.dataset.sortValue;
        if (raw === undefined || raw === "") {
            return null;
        }

        const numeric = Number(raw);
        return Number.isNaN(numeric) ? raw.toLowerCase() : numeric;
    }

    function compareRows(columnIndex, ascending) {
        return (rowA, rowB) => {
            const a = sortValue(rowA.cells[columnIndex]);
            const b = sortValue(rowB.cells[columnIndex]);

            if (a === null && b === null) return 0;
            if (a === null) return 1;
            if (b === null) return -1;
            if (a < b) return ascending ? -1 : 1;
            if (a > b) return ascending ? 1 : -1;
            return 0;
        };
    }

    function sortTable(table, columnIndex, ascending) {
        const tbody = table.tBodies[0];
        if (!tbody) return;

        const rows = Array.from(tbody.rows).filter((row) => !("sortExclude" in row.dataset));
        const excludedRows = Array.from(tbody.rows).filter((row) => "sortExclude" in row.dataset);

        rows.sort(compareRows(columnIndex, ascending));
        rows.forEach((row) => tbody.appendChild(row));
        excludedRows.forEach((row) => tbody.appendChild(row));
    }

    function initSortableTable(table) {
        const headers = Array.from(table.querySelectorAll("thead th.sortable-column"));

        headers.forEach((header) => {
            header.addEventListener("click", () => {
                const columnIndex = Array.from(header.parentElement.children).indexOf(header);
                const ascending = header.dataset.sortDirection !== "asc";

                headers.forEach((otherHeader) => {
                    delete otherHeader.dataset.sortDirection;
                    otherHeader.classList.remove("sorted-asc", "sorted-desc");
                });

                header.dataset.sortDirection = ascending ? "asc" : "desc";
                header.classList.add(ascending ? "sorted-asc" : "sorted-desc");

                sortTable(table, columnIndex, ascending);
            });
        });
    }

    document.querySelectorAll("table.sortable-table").forEach(initSortableTable);
})();

/**
 * CSV/Excel Export Utilities
 *
 * Provides functions to export data to CSV format for download
 */

/**
 * Convert an array of objects to CSV string
 */
export function convertToCSV(data: any[], headers?: string[]): string {
  if (data.length === 0) return "";

  // Get headers from first object if not provided
  const csvHeaders = headers || Object.keys(data[0]);

  // Create CSV header row
  const headerRow = csvHeaders.join(",");

  // Create CSV data rows
  const dataRows = data.map((row) => {
    return csvHeaders
      .map((header) => {
        const value = row[header];
        // Handle null/undefined
        if (value === null || value === undefined) return "";
        // Handle strings with commas, quotes, or newlines
        if (typeof value === "string" && (value.includes(",") || value.includes('"') || value.includes("\n"))) {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return value;
      })
      .join(",");
  });

  return [headerRow, ...dataRows].join("\n");
}

/**
 * Download CSV file
 */
export function downloadCSV(csvContent: string, filename: string): void {
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);

  link.setAttribute("href", url);
  link.setAttribute("download", filename);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

/**
 * Export data to CSV file
 */
export function exportToCSV(data: any[], filename: string, headers?: string[]): void {
  const csv = convertToCSV(data, headers);
  downloadCSV(csv, filename);
}

/**
 * Export table data to CSV
 * Useful for exporting data from existing HTML tables
 */
export function exportTableToCSV(tableId: string, filename: string): void {
  const table = document.getElementById(tableId) as HTMLTableElement;
  if (!table) {
    console.error(`Table with id "${tableId}" not found`);
    return;
  }

  const rows: string[] = [];

  // Get header row
  const headerCells = table.querySelectorAll("thead th");
  const headers = Array.from(headerCells).map((cell) => {
    const text = cell.textContent?.trim() || "";
    return text.includes(",") ? `"${text}"` : text;
  });
  rows.push(headers.join(","));

  // Get data rows
  const bodyRows = table.querySelectorAll("tbody tr");
  bodyRows.forEach((row) => {
    const cells = row.querySelectorAll("td");
    const rowData = Array.from(cells).map((cell) => {
      const text = cell.textContent?.trim() || "";
      return text.includes(",") ? `"${text}"` : text;
    });
    rows.push(rowData.join(","));
  });

  const csvContent = rows.join("\n");
  downloadCSV(csvContent, filename);
}

/**
 * Format data for export with custom transformations
 */
export function formatForExport<T>(
  data: T[],
  fieldMap: Record<string, (item: T) => any>
): any[] {
  return data.map((item) => {
    const exportRow: any = {};
    for (const [key, transformer] of Object.entries(fieldMap)) {
      exportRow[key] = transformer(item);
    }
    return exportRow;
  });
}

/**
 * Export chart of accounts to CSV
 */
export function exportAccountsToCSV(accounts: any[]): void {
  const exportData = formatForExport(accounts, {
    "Account Code": (a) => a.account_code,
    "Account Name": (a) => a.account_name,
    "Category": (a) => a.category,
    "Type": (a) => a.account_type,
    "Normal Balance": (a) => a.normal_balance,
    "Status": (a) => a.is_active ? "Active" : "Inactive",
    "Header": (a) => a.is_header ? "Yes" : "No",
    "System": (a) => a.is_system ? "Yes" : "No",
  });

  const filename = `chart-of-accounts-${new Date().toISOString().split("T")[0]}.csv`;
  exportToCSV(exportData, filename);
}

/**
 * Export journal entries to CSV
 */
export function exportJournalEntriesToCSV(entries: any[]): void {
  const exportData = formatForExport(entries, {
    "Entry Number": (e) => e.entry_number,
    "Date": (e) => e.entry_date,
    "Description": (e) => e.description || "",
    "Status": (e) => e.status,
    "Reference": (e) => e.reference_number || "",
    "Total Debit": (e) => e.total_debit || 0,
    "Total Credit": (e) => e.total_credit || 0,
    "Created At": (e) => e.created_at ? new Date(e.created_at).toLocaleString() : "",
  });

  const filename = `journal-entries-${new Date().toISOString().split("T")[0]}.csv`;
  exportToCSV(exportData, filename);
}

/**
 * Export petty cash vouchers to CSV
 */
export function exportPettyCashToCSV(vouchers: any[]): void {
  const exportData = formatForExport(vouchers, {
    "Voucher Number": (v) => v.voucher_number,
    "Date": (v) => v.voucher_date,
    "Description": (v) => v.description || "",
    "Amount": (v) => v.amount,
    "Status": (v) => v.status,
    "Payee": (v) => v.payee_name || "",
    "Category": (v) => v.category || "",
    "Branch": (v) => v.branch_id || "",
    "Created At": (v) => v.created_at ? new Date(v.created_at).toLocaleString() : "",
  });

  const filename = `petty-cash-vouchers-${new Date().toISOString().split("T")[0]}.csv`;
  exportToCSV(exportData, filename);
}

/**
 * Export commission rules to CSV
 */
export function exportCommissionRulesToCSV(rules: any[]): void {
  const exportData = formatForExport(rules, {
    "Rule Name": (r) => r.rule_name,
    "Type": (r) => r.commission_type,
    "Formula": (r) => r.formula_type,
    "Rate": (r) => r.rate || "",
    "Priority": (r) => r.priority,
    "Status": (r) => r.is_active ? "Active" : "Inactive",
    "Effective From": (r) => r.effective_from,
    "Effective Until": (r) => r.effective_until || "",
    "Applicable Roles": (r) => r.applicable_roles?.join("; ") || "",
  });

  const filename = `commission-rules-${new Date().toISOString().split("T")[0]}.csv`;
  exportToCSV(exportData, filename);
}

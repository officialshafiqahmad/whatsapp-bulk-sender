const HEADER_NAMES = new Set(["phone", "number", "mobile", "contact", "phone number", "whatsapp"]);

function cellValue(value) {
  if (value === null || value === undefined) return "";
  if (typeof value === "number" && Number.isInteger(value)) return String(value);
  return String(value).trim();
}

function normalizePhone(phone) {
  let cleaned = String(phone).trim().replace(/[\s\-()]/g, "");
  if (cleaned.startsWith("+")) cleaned = cleaned.slice(1);
  if (!/^\d+$/.test(cleaned)) {
    throw new Error(`Invalid phone number: ${phone}`);
  }
  if (cleaned.length < 8 || cleaned.length > 15) {
    throw new Error(`Phone number must be 8–15 digits: ${phone}`);
  }
  return cleaned;
}

function looksLikeHeader(value) {
  return HEADER_NAMES.has(String(value).trim().toLowerCase());
}

function parseExcelPhoneList(arrayBuffer, filename) {
  if (!filename.toLowerCase().endsWith(".xlsx") && !filename.toLowerCase().endsWith(".xlsm")) {
    throw {
      message: "Only Excel files (.xlsx) with a single column of phone numbers are accepted.",
      details: [`Received: ${filename}`, "Please export your list as .xlsx with one column only."],
    };
  }

  if (typeof XLSX === "undefined") {
    throw {
      message: "Excel reader is not loaded.",
      details: ["Refresh the page and try again."],
    };
  }

  let workbook;
  try {
    workbook = XLSX.read(arrayBuffer, { type: "array" });
  } catch (error) {
    throw {
      message: "Could not read the Excel file. Make sure it is a valid .xlsx file.",
      details: [String(error.message || error)],
    };
  }

  const sheet = workbook.Sheets[workbook.SheetNames[0]];
  const rows = XLSX.utils.sheet_to_json(sheet, { header: 1, raw: false, defval: "" });

  if (!rows.length) {
    throw { message: "The Excel file is empty.", details: [] };
  }

  const parsedRows = [];
  const nonEmptyColumns = new Set();

  for (const row of rows) {
    const values = row.map(cellValue);
    while (values.length && !values[values.length - 1]) values.pop();
    if (!values.some(Boolean)) continue;

    parsedRows.push(values);
    values.forEach((value, index) => {
      if (value) nonEmptyColumns.add(index);
    });
  }

  if (!parsedRows.length) {
    throw { message: "The Excel file has no phone numbers.", details: [] };
  }

  if (nonEmptyColumns.size > 1) {
    throw {
      message: "The Excel file must contain only one column of phone numbers.",
      details: [
        `Found data in ${nonEmptyColumns.size} columns.`,
        "Remove extra columns and keep only phone numbers in column A.",
      ],
    };
  }

  let startIndex = 0;
  if (parsedRows[0][0] && looksLikeHeader(parsedRows[0][0])) {
    startIndex = 1;
  }

  const numbers = [];
  const errors = [];

  for (let i = startIndex; i < parsedRows.length; i += 1) {
    const row = parsedRows[i];
    const rowNumber = i + 1;

    if (row.length > 1 && row.slice(1).some(Boolean)) {
      throw {
        message: "The Excel file must contain only one column of phone numbers.",
        details: [`Extra data found on row ${rowNumber}.`],
      };
    }

    const raw = row[0] || "";
    if (!raw) continue;

    try {
      numbers.push(normalizePhone(raw));
    } catch (error) {
      errors.push(`Row ${rowNumber}: ${error.message}`);
    }
  }

  if (errors.length) {
    throw {
      message: "Some phone numbers in the Excel file are invalid.",
      details: errors.slice(0, 20).concat(errors.length > 20 ? ["..."] : []),
    };
  }

  if (!numbers.length) {
    throw { message: "No valid phone numbers were found in the Excel file.", details: [] };
  }

  const deduped = [];
  const seen = new Set();
  for (const number of numbers) {
    if (!seen.has(number)) {
      seen.add(number);
      deduped.push(number);
    }
  }

  return deduped;
}

window.parseExcelPhoneList = parseExcelPhoneList;

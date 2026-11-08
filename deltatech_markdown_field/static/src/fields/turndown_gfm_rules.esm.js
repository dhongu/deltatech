/** @odoo-module **/

/**
 * GitHub Flavored Markdown rules for turndown.
 *
 * marked renders strikethrough, tables and task lists (gfm: true), but turndown
 * core has no rule for them and keeps only their text. Without these rules the
 * HTML -> Markdown step on blur would flatten them in the stored value.
 *
 * A table that GFM cannot express (merged cells, block content in a cell,
 * rows of different length) is kept as HTML instead of being flattened.
 */

const CELL_TAGS = ["TH", "TD"];
const BLOCK_IN_CELL = "p, div, ul, ol, li, pre, blockquote, table, h1, h2, h3, h4, h5, h6, hr";

function closestTable(node) {
    return node.closest ? node.closest("table") : null;
}

function isSimpleTable(table) {
    if (!table || !table.rows || !table.rows.length) {
        return false;
    }
    const width = table.rows[0].cells.length;
    if (!width) {
        return false;
    }
    for (const row of table.rows) {
        if (closestTable(row) !== table || row.cells.length !== width) {
            return false;
        }
        for (const cell of row.cells) {
            if (cell.rowSpan > 1 || cell.colSpan > 1 || cell.querySelector(BLOCK_IN_CELL)) {
                return false;
            }
        }
    }
    return true;
}

function inSimpleTable(node) {
    return isSimpleTable(closestTable(node));
}

function cellAlignment(cell) {
    const align = (cell.getAttribute("align") || cell.style.textAlign || "").toLowerCase();
    if (align === "left") {
        return ":---";
    }
    if (align === "right") {
        return "---:";
    }
    if (align === "center") {
        return ":---:";
    }
    return "---";
}

function isTaskCheckbox(node) {
    if (node.nodeName !== "INPUT" || (node.getAttribute("type") || "").toLowerCase() !== "checkbox") {
        return false;
    }
    const parent = node.parentNode;
    if (!parent) {
        return false;
    }
    if (parent.nodeName === "LI") {
        return true;
    }
    // Loose lists: <li><p><input> text</p></li>
    return parent.nodeName === "P" && parent.parentNode && parent.parentNode.nodeName === "LI";
}

export function addGfmRules(turndownService) {
    turndownService.addRule("gfmStrikethrough", {
        filter: ["del", "s", "strike"],
        replacement: (content) => (content.trim() ? `~~${content}~~` : content),
    });

    turndownService.addRule("gfmTaskListItem", {
        filter: isTaskCheckbox,
        replacement: (content, node) => {
            const checked = node.checked || node.hasAttribute("checked");
            const next = node.nextSibling;
            const space = next && next.nodeType === Node.TEXT_NODE && /^\s/.test(next.nodeValue) ? "" : " ";
            return `${checked ? "[x]" : "[ ]"}${space}`;
        },
    });

    turndownService.addRule("gfmTableCell", {
        filter: (node) => CELL_TAGS.includes(node.nodeName) && inSimpleTable(node),
        replacement: (content, node) => {
            const text = content.trim().replace(/\n+/g, " ").replace(/\|/g, "\\|");
            const first = node.parentNode.cells[0] === node;
            return `${first ? "| " : " "}${text} |`;
        },
    });

    turndownService.addRule("gfmTableRow", {
        filter: (node) => node.nodeName === "TR" && inSimpleTable(node),
        replacement: (content, node) => {
            const table = closestTable(node);
            if (table.rows[0] !== node) {
                return `\n${content}`;
            }
            const separator = [...node.cells].map(cellAlignment).join(" | ");
            return `\n${content}\n| ${separator} |`;
        },
    });

    turndownService.addRule("gfmTableSection", {
        filter: (node) => ["THEAD", "TBODY", "TFOOT"].includes(node.nodeName) && inSimpleTable(node),
        replacement: (content) => content,
    });

    turndownService.addRule("gfmTable", {
        filter: (node) => node.nodeName === "TABLE" && isSimpleTable(node),
        replacement: (content) => `\n\n${content.replace(/^\n+/, "")}\n\n`,
    });

    // Tables GFM cannot express stay as HTML (marked renders them back as such).
    turndownService.keep((node) => node.nodeName === "TABLE" && !isSimpleTable(node));

    return turndownService;
}

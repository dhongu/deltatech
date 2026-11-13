import {Component, useState} from "@odoo/owl";
import {Dialog} from "@web/core/dialog/dialog";
import {_t} from "@web/core/l10n/translation";
import {useService} from "@web/core/utils/hooks";
import {usePos} from "@point_of_sale/app/hooks/pos_hook";

export class StockOpsDialog extends Component {
    static template = "deltatech_pos_stock_ops.StockOpsDialog";
    static components = {Dialog};
    static props = {
        operationType: String, // "receipt" | "delivery"
        close: Function,
    };

    setup() {
        this.pos = usePos();
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({
            search: "",
            partner: null,
            lines: [],
            busy: false,
            // Receipts only: the transfer of a purchase order being received.
            picking: null,
            pickings: [],
        });
        if (this.isReceipt) {
            this.searchPickings("");
        }
    }

    get placeholderOrders() {
        return _t("Search a purchase order or a supplier");
    }

    get placeholderProducts() {
        return _t("Scan a barcode or type a product");
    }

    get isReceipt() {
        return this.props.operationType === "receipt";
    }

    async searchPickings(term) {
        this.state.pickings = await this.orm.call("pos.stock.operation", "pos_search_receipts", [
            this.pos.config.id,
            term,
        ]);
    }

    selectPicking(picking) {
        this.state.picking = picking;
        this.state.lines = picking.moves.map((move) => ({
            moveId: move.id,
            productId: move.product_id,
            name: move.name,
            demand: move.qty,
            qty: move.qty,
            uomName: move.uom_name,
        }));
        this.state.search = "";
    }

    backToOrders() {
        this.state.picking = null;
        this.state.lines = [];
    }

    get title() {
        return this.props.operationType === "receipt" ? _t("Receipt") : _t("Delivery");
    }

    get suggestions() {
        const word = this.state.search.trim().toLowerCase();
        if (word.length < 2) {
            return [];
        }
        return this.pos.models["product.product"]
            .filter(
                (p) =>
                    (p.display_name || "").toLowerCase().includes(word) ||
                    (p.default_code || "").toLowerCase().includes(word)
            )
            .slice(0, 8);
    }

    /** Pack = a unit of measure linked to the product, with its own barcode. */
    packsOf(product) {
        return this.pos.models["product.uom"].filter((u) => u.product_id?.id === product.id);
    }

    onSearchKeydown(ev) {
        if (ev.key !== "Enter") {
            return;
        }
        const code = this.state.search.trim();
        if (this.isReceipt && !this.state.picking) {
            this.searchPickings(code);
            return;
        }
        if (!code) {
            return;
        }
        if (this.isReceipt) {
            this.scanReceived(code);
            return;
        }
        const product = this.pos.models["product.product"].getBy("barcode", code);
        if (product) {
            this.addLine(product);
            return;
        }
        const pack = this.pos.models["product.uom"].getBy("barcode", code);
        if (pack) {
            this.addLine(pack.product_id, pack.uom_id);
            return;
        }
        const found = this.suggestions;
        if (found.length === 1) {
            this.addLine(found[0]);
            return;
        }
        this.notification.add(_t("No product found for %s.", code), {type: "warning"});
    }

    /** Receipts: a scanned barcode adds one to the matching line of the order. */
    scanReceived(code) {
        const product =
            this.pos.models["product.product"].getBy("barcode", code) ||
            this.pos.models["product.uom"].getBy("barcode", code)?.product_id;
        const line = product && this.state.lines.find((l) => l.productId === product.id);
        if (!line) {
            this.notification.add(_t("%s is not on this purchase order.", code), {type: "warning"});
            return;
        }
        line.qty = this.state.lines.some((l) => l === line && l.scanned) ? line.qty + 1 : 1;
        line.scanned = true;
        this.state.search = "";
    }

    addLine(product, uom = null) {
        const uomId = uom?.id || product.uom_id?.id;
        const line = this.state.lines.find((l) => l.product.id === product.id && l.uomId === uomId);
        if (line) {
            line.qty += 1;
        } else {
            this.state.lines.push({product, qty: 1, uomId});
        }
        this.state.search = "";
    }

    uomName(line) {
        if (line.uomName) {
            return line.uomName;
        }
        const uom = this.pos.models["uom.uom"].get(line.uomId);
        return uom?.name || "";
    }

    removeLine(line) {
        this.state.lines = this.state.lines.filter((l) => l !== line);
    }

    onQtyChange(line, ev) {
        const value = parseFloat(ev.target.value);
        line.qty = value > 0 || (this.isReceipt && value === 0) ? value : 1;
    }

    async selectPartner() {
        const partner = await this.pos.selectPartner();
        if (partner) {
            this.state.partner = partner;
        }
    }

    async confirm() {
        if (!this.state.lines.length || this.state.busy) {
            return;
        }
        this.state.busy = true;
        try {
            const result = this.isReceipt
                ? await this.orm.call("pos.stock.operation", "pos_receive_picking", [
                      this.pos.config.id,
                      this.state.picking.id,
                      this.state.lines.map((l) => ({move_id: l.moveId, qty: l.qty})),
                  ])
                : await this.orm.call("pos.stock.operation", "pos_create_operation", [
                      this.pos.config.id,
                      this.props.operationType,
                      this.state.partner?.id || false,
                      this.state.lines.map((l) => ({
                          product_id: l.product.id,
                          qty: l.qty,
                          uom_id: l.uomId,
                      })),
                  ]);
            this.notification.add(result.message, {
                type: result.state === "done" ? "success" : "warning",
            });
            this.props.close();
        } finally {
            this.state.busy = false;
        }
    }
}

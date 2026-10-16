/** @odoo-module **/

// Shared by the card, the filter and the offline popup, so the three always agree on what
// "in stock" means for a given register.

/** Is the "other shops" stock switched on for this register? */
export function hasShopStock(config) {
    return Boolean(config?.display_stock && config.stock_shop_list?.length);
}

/** The quantity of this shop, the same figure the badge of deltatech_pos_stock shows. */
export function localStockQuantity(config, product) {
    if (!product) {
        return 0;
    }
    const useFreeQty = config?.stock_badge_quantity === "available";
    return (useFreeQty ? product.free_qty : product.qty_available) || 0;
}

/** Quantity of the product in one of the other shops. */
export function shopStockQuantity(product, warehouseId) {
    return product?.pos_shop_stock?.[String(warehouseId)] || 0;
}

/**
 * What the other shops have, together. Negative stock in one shop (sold before the receipt
 * was booked) does not take anything away from what another shop can actually hand over.
 */
export function shopStockTotal(config, product) {
    let total = 0;
    for (const shop of config?.stock_shop_list || []) {
        total += Math.max(shopStockQuantity(product, shop.id), 0);
    }
    return Math.round(total * 1000) / 1000;
}

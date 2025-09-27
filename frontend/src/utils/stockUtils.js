// src/utils/stockUtils.js
import axios from 'axios';

/**
 * Adjust inventory for a set of order items.
 *
 * @param {Array} items      order.items array
 * @param {number} factor    +1 to add back, -1 to subtract
 */
export async function adjustStockForOrder(items, factor) {
  const adj = {};

  items.forEach(it => {
    if (it.itemType === 'Product') {
      const id = it.itemId._id || it.itemId;
      adj[id] = (adj[id] || 0) + factor * (it.quantity || 1);
    }
    // handle other itemTypes/specs here if needed
  });

  await Promise.all(
    Object.entries(adj).map(([productId, change]) =>
      axios.patch(
        `http://localhost:5000/api/products/${productId}/inventory`,
        { change }    // backend should apply displayedStock += change
      )
    )
  );
}

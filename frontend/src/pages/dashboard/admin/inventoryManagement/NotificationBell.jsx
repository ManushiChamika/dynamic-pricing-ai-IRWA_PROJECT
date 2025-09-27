// NotificationBell.jsx
import { useState } from "react";
import LowStockModal from "./LowStockModal";

const NotificationBell = ({ products, onSaveProducts }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  // now look at the same field you're rendering in your table:
  const lowStockProducts = products.filter(
    p => p.displayedStock <= (p.threshold ?? 3)
  );

  return (
    <div className="relative">
      <button
        onClick={() => setIsModalOpen(true)}
        className="relative focus:outline-none"
      >
        {/* your bell SVG */}
        {lowStockProducts.length > 0 && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-red-100 bg-red-600 rounded-full">
            {lowStockProducts.length}
          </span>
        )}
      </button>

      {isModalOpen && (
        <LowStockModal
          lowStockProducts={lowStockProducts}
          onClose={() => setIsModalOpen(false)}
          onSaveProducts={onSaveProducts}
        />
      )}
    </div>
  );
};

export default NotificationBell;

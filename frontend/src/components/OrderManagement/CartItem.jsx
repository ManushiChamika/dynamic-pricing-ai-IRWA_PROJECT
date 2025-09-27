import React, { useState, useEffect } from "react";

const CartItem = ({ item, specs = [], updateQuantity }) => {
  const [showBulkOrderMessage, setShowBulkOrderMessage] = useState(false);

    /**
   * 
   * ToDo: Thi part got added
   * 
   * 
   */
    const requiredLabels = [
      "Processor",
      "GPU",
      "RAM",
      "Storage",
      "Power Supply",
      "Casing",
    ];
  
    /**
     * 
     * ToDo: Thi part got added
     * 
     * 
     */
  
    // Only render if every one of those labels exists in specs
    const hasAllSpecs = requiredLabels.every(label =>
      specs.some(s => s.label === label)
    );
  
  // Ensure quantity is treated as a number
  const initialQuantity = parseInt(item.quantity, 10) || 1;
  const [quantity, setQuantity] = useState(initialQuantity);

  const effectivePrice = item.discountPrice ? item.discountPrice : item.price;

  // Track previous quantity to avoid infinite loop
  const [prevQuantity, setPrevQuantity] = useState(quantity);

  useEffect(() => {
    if (quantity !== prevQuantity) {
      // Prevent infinite loop by updating only when the quantity changes
      if (quantity > item.displayedStock) {
        setShowBulkOrderMessage(true);
      } else {
        setShowBulkOrderMessage(false);
      }

      // Update the parent component with the new quantity
      updateQuantity(item._id, quantity); // Pass item id and updated quantity
      setPrevQuantity(quantity); // Update prevQuantity to the current one
    }
  }, [quantity, item._id, item.displayedStock, prevQuantity, updateQuantity]);

  const handleQuantityChange = (e) => {
    let newQuantity = parseInt(e.target.value, 100);

    if (isNaN(newQuantity) || newQuantity < 1) {
      return; // Prevent invalid input
    }

    if (newQuantity <= item.displayedStock) {
      setQuantity(newQuantity); // Update local state only if valid
    } else {
      setShowBulkOrderMessage(true); // Show bulk order message if the quantity exceeds stock
    }
  };

  const handleQuantityIncrement = () => {
    if (quantity < item.displayedStock) {
      setQuantity(quantity + 1);
    }
  };

  const handleQuantityDecrement = () => {
    if (quantity > 1) {
      setQuantity(quantity - 1);
    }
  };

  return (
    <div className="relative">
      <div className="flex gap-4 items-center border border-gray-700 p-4 rounded shadow-sm bg-gray-900 text-white">
        {item.image && (
          <img
            src={item.image}
            alt={item.description || "Item"}
            className="w-20 h-20 object-cover rounded"
          />
        )}

        {/* /**
      * 
      * ToDo: This part got added
      * 
      * 
      */ }
        {/* Only show specs if all six are present */}
      {hasAllSpecs && (
        <ul className="mt-2 text-sm text-gray-300">
          {requiredLabels.map(label => {
            const spec = specs.find(s => s.label === label);
            return (
              <li key={label} className="flex">
                <span className="w-24 font-mono text-gray-500">{label}:</span>
                <span className="font-medium">{spec.value}</span>
              </li>
            );
          })}
        </ul>
      )}

        <div className="flex-1">
          {item.description && <p className="text-gray-400">{item.description}</p>}
          {item.displayedStock !== undefined && (
            <p className="text-sm text-gray-500">Stock: {item.displayedStock}</p>
          )}
          {effectivePrice !== undefined && (
            <p className="text-xl font-semibold text-green-400">LKR {effectivePrice}</p>
          )}
        </div>

        {/* Quantity controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={handleQuantityDecrement}
            disabled={quantity <= 1}
            className="bg-gray-600 text-white px-3 py-1 rounded hover:bg-gray-500 transition-all"
          >
            -
          </button>

          <input
            type="number"
            min="1"
            max={item.displayedStock}
            value={quantity}
            onChange={handleQuantityChange}
            className="w-16 p-1 border border-gray-600 rounded bg-gray-800 text-white focus:ring focus:ring-green-500"
          />

          <button
            onClick={handleQuantityIncrement}
            disabled={quantity >= item.displayedStock}
            className="bg-gray-600 text-white px-3 py-1 rounded hover:bg-gray-500 transition-all"
          >
            +
          </button>
        </div>
      </div>

      {showBulkOrderMessage && (
        <p className="text-sm text-red-500 mt-2">
          You cannot order more than {item.displayedStock} of this item.
        </p>
      )}
    </div>
  );
};

export default CartItem;

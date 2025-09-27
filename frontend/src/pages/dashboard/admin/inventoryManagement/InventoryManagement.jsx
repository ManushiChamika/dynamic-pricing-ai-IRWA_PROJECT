import { useState, useEffect } from "react";
import axios from "axios";
import PropTypes from "prop-types";

const InventoryProductModal = ({ product, onClose, onProductUpdated }) => {
  // Read-only fields.
  const [_id] = useState(product._id);
  const [description] = useState(product.description);
  const [price] = useState(product.price);

  // Editable fields.
  const [discount, setDiscount] = useState(product.discount || 0);
  const [discountPrice, setDiscountPrice] = useState(
    product.discountPrice || product.price
  );
  const [displayedStock, setDisplayedStock] = useState(product.displayedStock || 0);

  // Error and loading states.
  const [discountError, setDiscountError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Recalculate discount price whenever discount or price changes.
  useEffect(() => {
    const discPrice = price - (price * discount) / 100;
    setDiscountPrice(Number(discPrice.toFixed(2)));
  }, [price, discount]);

  // Save changes: update product inventory on the backend.
  const handleSave = async (e) => {
    e.preventDefault();
    if (discountError) return;
    setIsLoading(true);
    try {
      const updateProduct = {
        discount,
        discountPrice,
        displayedStock,
      };

      const response = await axios.patch(
        `http://localhost:5000/api/products/${_id}/inventory`,
        updateProduct
      );

      if (response.status === 200) {
        alert("Product inventory updated successfully!");
        if (typeof onProductUpdated === "function") {
          onProductUpdated(response.data);
        }
        onClose();
      }
    } catch (error) {
      console.error("❌ Error updating product:", error.message);
      if (error.response) {
        console.error("Response data:", error.response.data);
      }
      alert("Error updating product inventory. Check console for details.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* Main Modal */}
      <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-20 z-50">
        <div className="bg-white p-8 rounded-md w-7/12 relative">
          <h3 className="text-2xl font-bold mb-4">Inventory Management</h3>

          {/* Product ID (Read-only) */}
          <div className="mb-4">
            <label className="block text-lg font-medium text-gray-700">
              Product ID:
            </label>
            <input
              type="text"
              value={_id}
              readOnly
              className="w-full p-2 border rounded-md bg-gray-200"
            />
          </div>

          {/* Description (Read-only) */}
          <div className="mb-4">
            <label className="block text-lg font-medium text-gray-700">
              Description:
            </label>
            <input
              type="text"
              value={description}
              readOnly
              className="w-full p-2 border rounded-md bg-gray-200"
            />
          </div>

          {/* Price (Read-only) */}
          <div className="mb-4">
            <label className="block text-lg font-medium text-gray-700">
              Price:
            </label>
            <input
              type="number"
              value={price}
              readOnly
              className="w-full p-2 border rounded-md"
            />
          </div>

          {/* Discount (Editable) */}
          <div className="mb-4">
            <label className="block text-lg font-medium text-gray-700">
              Discount (%):
            </label>
            <input
              type="number"
              value={discount}
              onChange={(e) => {
                const newDiscount = Number(e.target.value);
                if (newDiscount < 0) {
                  setDiscountError("Discount cannot be less than 0");
                } else {
                  setDiscountError("");
                  setDiscount(newDiscount);
                }
              }}
              className="w-full p-2 border rounded-md"
            />
            {discountError && (
              <p className="mt-1 text-red-500 text-sm">{discountError}</p>
            )}
          </div>

          {/* Discounted Price (Read-only) */}
          <div className="mb-4">
            <label className="block text-lg font-medium text-gray-700">
              Discount Price:
            </label>
            <input
              type="number"
              value={discountPrice}
              readOnly
              className="w-full p-2 border rounded-md bg-gray-200"
            />
          </div>

          {/* Displayed Stock (Editable) */}
          <div className="mb-4">
            <label className="block text-lg font-medium text-gray-700">
              Customer Visible Stock:
            </label>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setDisplayedStock(Math.max(displayedStock - 1, 0))}
                className="px-2 py-1 bg-red-600 text-white rounded-md"
              >
                -
              </button>
              <input
                type="number"
                value={displayedStock}
                onChange={(e) => setDisplayedStock(Number(e.target.value))}
                className="w-20 p-2 border rounded-md text-center"
              />
              <button
                onClick={() => setDisplayedStock(displayedStock + 1)}
                className="px-2 py-1 bg-green-600 text-white rounded-md"
              >
                +
              </button>
            </div>
            <small className="text-gray-500">
              This stock is what the customers will see.
            </small>
          </div>

          {/* Buttons */}
          <div className="flex justify-end space-x-4">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-300 rounded-md"
              disabled={isLoading}
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-2 bg-blue-600 text-white rounded-md"
              disabled={isLoading || discountError}
            >
              {isLoading ? "Saving..." : "Save"}
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

InventoryProductModal.propTypes = {
  product: PropTypes.object.isRequired,
  onClose: PropTypes.func.isRequired,
  onProductUpdated: PropTypes.func,
};

InventoryProductModal.defaultProps = {
  onProductUpdated: () => {},
};

export default InventoryProductModal;

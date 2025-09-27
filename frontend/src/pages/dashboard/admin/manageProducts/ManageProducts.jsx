import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { FaPlus, FaBoxes } from "react-icons/fa";
import EditProductModal from "./EditProductModal";
import InventoryManagement from "../inventoryManagement/InventoryManagement";

const ManageProducts = () => {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [filterCategory, setFilterCategory] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedProductForEdit, setSelectedProductForEdit] = useState(null);
  const [selectedProductForInventory, setSelectedProductForInventory] = useState(null);
  const [deleteProductId, setDeleteProductId] = useState(null); // For delete confirmation popup

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get("http://localhost:5000/api/products");
      if (response.status === 200) {
        setProducts(response.data);
      }
    } catch (error) {
      console.error("Error fetching products:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // Called when user confirms deletion in the popup
  const confirmDelete = async () => {
    try {
      await axios.delete(`http://localhost:5000/api/products/${deleteProductId}`);
      fetchProducts();
    } catch (error) {
      console.error("Error deleting product:", error);
      window.alert("Error deleting product.");
    } finally {
      setDeleteProductId(null);
    }
  };

  const handleEdit = (productId) => {
    const productToEdit = products.find((p) => p._id === productId);
    setSelectedProductForEdit(productToEdit);
  };

  const handleInventory = (productId) => {
    const inventory = products.find((p) => p._id === productId);
    setSelectedProductForInventory(inventory);
  };

  // Helper function to render specs by normalizing data to an array.
  const renderSpecs = (specs) => {
    if (!specs) return null;
    const normalizeSpecs = (specs) => {
      if (!specs) return [];
      if (Array.isArray(specs)) return specs;
      if (typeof specs === "object") return [specs];
      return [];
    };

    const normalizedSpecs = normalizeSpecs(specs);

    return normalizedSpecs.map((spec, idx) => (
      <div key={idx}>
        {spec.key}: {spec.value}
      </div>
    ));
  };

  const filteredProducts = filterCategory
    ? products.filter((p) => p.category === filterCategory)
    : products;

  return (
    <>
      {selectedProductForEdit && (
        <EditProductModal
          product={selectedProductForEdit}
          onClose={() => setSelectedProductForEdit(null)}
          onProductUpdated={(updatedProduct) =>
            setProducts((prev) =>
              prev.map((p) =>
                p._id === updatedProduct._id ? updatedProduct : p
              )
            )
          }
        />
      )}

      {selectedProductForInventory && (
        <InventoryManagement
          product={selectedProductForInventory}
          onClose={() => setSelectedProductForInventory(null)}
          onInventoryUpdated={(updatedProduct) =>
            setProducts((prev) =>
              prev.map((p) =>
                p._id === updatedProduct._id ? updatedProduct : p
              )
            )
          }
        />
      )}

      {/* Delete confirmation popup */}
      {deleteProductId && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.8)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
          }}
        >
          <div
            style={{
              background: "white",
              padding: "20px",
              borderRadius: "8px",
              textAlign: "center",
              boxShadow: "0 2px 8px rgba(0, 0, 0, 0.26)",
              width: "300px",
            }}
          >
            <p style={{ marginBottom: "20px" }}>
              Are you sure you want to delete this product?
            </p>
            <div style={{ display: "flex", justifyContent: "space-around" }}>
              <button
                onClick={() => setDeleteProductId(null)}
                style={{
                  padding: "8px 16px",
                  backgroundColor: "#a0aec0",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
                }}
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                style={{
                  padding: "8px 16px",
                  backgroundColor: "#e53e3e",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
                }}
              >
                Ok
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="min-h-screen bg-gray-50 py-12 px-6">


        <h2 className="text-4xl font-bold text-center text-blue-800 mb-10">
          Manage Products
        </h2>
        <div className="max-w-7xl mx-auto bg-white shadow-xl rounded-lg p-8">
          <div className="mb-6">
            <label className="block text-lg font-medium text-gray-700 mb-2">
              Filter by Category:
            </label>
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="w-full p-2 border rounded-md"
            >
              <option value="">All Categories</option>
              {Array.from(new Set(products.map((p) => p.category))).map(
                (cat, idx) => (
                  <option key={idx} value={cat}>
                    {cat.toUpperCase()}
                  </option>
                )
              )}
            </select>
          </div>
          {isLoading ? (
            <p className="text-center text-gray-600">Loading products...</p>
          ) : (
            <table className="min-w-full border-collapse border border-gray-300">
              <thead className="bg-gray-100">
                <tr>
                  <th className="border p-2">Image</th>
                  <th className="border p-2">Name of Product</th>
                  <th className="border p-2">Availability</th>
                  <th className="border p-2">State</th>
                  <th className="border p-2">Specs</th>
                  <th className="border p-2">Price</th>
                  <th className="border p-2">Actions</th>
                </tr>
              </thead>
              <tbody>
  {filteredProducts.map((product) => (
    <tr key={product._id} className="hover:bg-gray-50">
      <td className="border p-2">
        {product.image && (
          <img
            src={product.image}
            alt={product.description}
            className="h-16 w-16 object-cover rounded-md"
          />
        )}
      </td>
      <td className="border p-2">{product.description}</td>
      <td className="border p-2">{product.availability}</td>
      <td className="border p-2">{product.state}</td>
      <td className="border p-2">{renderSpecs(product.specs)}</td>
      <td className="border p-2">
        LKR {Number(product.price).toFixed(2)}
      </td>
      <td className="border p-2 flex flex-col space-y-2">
        <div className="flex space-x-2">
          <button
            onClick={() => handleEdit(product._id)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-500"
          >
            Edit
          </button>
          <button
            onClick={() => setDeleteProductId(product._id)}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-500"
          >
            Delete
          </button>
        </div>
        <button
          onClick={() => handleInventory(product._id)}
          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-500"
        >
          Manage Inventory
        </button>
      </td>
    </tr>
  ))}
</tbody>

            </table>
          )}
        </div>
      </div>
    </>
  );
};

export default ManageProducts;

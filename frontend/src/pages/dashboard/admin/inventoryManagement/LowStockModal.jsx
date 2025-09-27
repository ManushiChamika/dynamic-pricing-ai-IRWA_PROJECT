import React, { useState, useEffect, useCallback, useMemo } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import InventoryProductModal from "./InventoryManagement";

// API base
const API_URL = "http://localhost:5000/api";
// Storage helpers for order-button state
const STORAGE_KEY = "orderStatusMap";
const loadStatusMap = () => {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
  } catch {
    return {};
  }
};
const saveStatusMap = (map) => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(map));
};
// Helper for auth headers
const getAuthHeaders = () => {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export default function InventoryTable() {
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [showOrdersModal, setShowOrdersModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [filterCategory, setFilterCategory] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  // Fetch products
  const fetchProducts = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await axios.get(`${API_URL}/products`);
      setProducts(
        res.data.map((p) => ({
          ...p,
          displayedStock: p.displayedStock ?? 0,
          threshold: p.threshold ?? 3,
        }))
      );
    } catch (e) {
      console.error(e);
      alert("Failed to load products");
    } finally {
      setIsLoading(false);
    }
  }, []);
  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  // Save low-stock adjustments
  const handleSaveProducts = useCallback(async (updatedOnes) => {
    setProducts((prev) =>
      prev.map((p) => {
        const u = updatedOnes.find((x) => x._id === p._id);
        return u
          ? { ...p, displayedStock: u.displayedStock, availability: u.availability || p.availability }
          : p;
      })
    );
    // Persist inventory and availability
    await Promise.all(
      updatedOnes.map((p) =>
        Promise.all([
          axios.patch(
            `${API_URL}/products/${p._id}/inventory`,
            { displayedStock: p.displayedStock },
            { headers: getAuthHeaders() }
          ),
          p.availability
            ? axios.patch(
                `${API_URL}/products/${p._id}`,
                { availability: p.availability },
                { headers: getAuthHeaders() }
              )
            : Promise.resolve(),
        ])
      )
    );
  }, []);

  // Mark out of stock (updates both stock and availability)
  const handleMarkOutOfStock = async (productId) => {
    try {
      // 1. Set availability = 'out of stock'
      await axios.patch(
        `${API_URL}/products/${productId}`,
        { availability: 'out of stock' },
        { headers: getAuthHeaders() }
      );
      // 2. Set displayedStock = 0
      await axios.patch(
        `${API_URL}/products/${productId}/inventory`,
        { displayedStock: 0 },
        { headers: getAuthHeaders() }
      );
      // Update UI state
      setProducts((prev) =>
        prev.map((p) =>
          p._id === productId
            ? { ...p, displayedStock: 0, availability: 'out of stock' }
            : p
        )
      );
    } catch (err) {
      console.error("Failed to mark out of stock:", err);
      alert("Could not mark product as out of stock.");
    }
  };

  // Filtering logic
  const filtered = products
    .filter((p) => (filterCategory ? p.category === filterCategory : true))
    .filter((p) => p.description.toLowerCase().includes(searchQuery.toLowerCase()));

  return (
    <div className="p-4">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-3xl font-bold text-blue-900">Product Inventory</h2>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowOrdersModal(true)}
            className="px-4 py-2 bg-indigo-600 text-white rounded"
          >
            Manage Orders
          </button>
          {/* NotificationBell omitted for brevity */}
        </div>
      </div>

      {/* Search & Filter */}
      <input
        type="text"
        placeholder="Search products…"
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        className="w-full mb-4 p-2 border rounded"
      />
      <select
        value={filterCategory}
        onChange={(e) => setFilterCategory(e.target.value)}
        className="w-full mb-4 p-2 border rounded"
      >
        <option value="">All Categories</option>
        {[...new Set(products.map((p) => p.category))].map((cat) => (
          <option key={cat} value={cat}>
            {cat}
          </option>
        ))}
      </select>

      {/* Product Table */}
      {isLoading ? (
        <p>Loading…</p>
      ) : (
        <table className="min-w-full border border-gray-300">
          <thead className="bg-gray-100">
            <tr>
              <th className="p-2 border">ID</th>
              <th className="p-2 border">Description</th>
              <th className="p-2 border">Stock</th>
              <th className="p-2 border">Threshold</th>
              <th className="p-2 border">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((p) => (
              <tr
                key={p._id}
                className={`hover:bg-gray-50 ${p.displayedStock <= 0 ? 'bg-yellow-300' : p.displayedStock <= p.threshold ? 'bg-red-100' : ''}`}
              >
                <td className="p-2 border">{p._id}</td>
                <td className="p-2 border">{p.description}</td>
                <td className="p-2 border">{p.displayedStock}</td>
                <td className="p-2 border">{p.threshold}</td>
                <td className="p-2 border space-y-2">
                  {p.displayedStock <= 0 ? (
                    <button
                      onClick={() => handleMarkOutOfStock(p._id)}
                      className="w-full py-1 bg-red-600 text-white rounded"
                    >
                      Mark Out of Stock
                    </button>
                  ) : (
                    <button
                      onClick={() => setSelectedProduct(p)}
                      className="w-full py-1 bg-blue-600 text-white rounded"
                    >
                      Edit
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Edit-product modal */}
      {selectedProduct && (
        <InventoryProductModal
          product={selectedProduct}
          onClose={() => setSelectedProduct(null)}
          onProductUpdated={(upd) => {
            if (upd) {
              setProducts((prev) =>
                prev.map((p) => (p._id === upd._id ? upd : p))
              );
            }
            setSelectedProduct(null);
          }}
        />
      )}
    </div>
  );
}

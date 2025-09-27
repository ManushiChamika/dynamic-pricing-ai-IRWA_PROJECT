// src/components/InventoryTable.jsx
import React, { useState, useEffect, useCallback, useMemo } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import InventoryProductModal from "./InventoryManagement";
import "jspdf-autotable";
import { jsPDF } from "jspdf";

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

// Low-stock adjustment modal
const LowStockModal = ({ lowStockProducts, onClose, onSaveProducts }) => {
  const [localList, setLocalList] = useState(
    lowStockProducts.map((p) => ({ ...p }))
  );
  const threshold = 3;

  const handleChange = (id, value) => {
    setLocalList((list) =>
      list.map((p) =>
        p._id === id ? { ...p, displayedStock: Number(value) } : p
      )
    );
  };

  const handleSave = () => {
    const below = localList.filter((p) => p.displayedStock < threshold);
    if (below.length > 0) {
      const names = below.map((p) => p.description || p._id).join(", ");
      const confirmMark = window.confirm(
        `The following products are below the minimum stock of ${threshold}: ${names}.\n` +
          `Would you like to mark them as out of stock?`
      );
      if (confirmMark) {
        const updated = localList.map((p) =>
          p.displayedStock < threshold
            ? { ...p, displayedStock: 0, availability: "out of stock" }
            : p
        );
        onSaveProducts(updated);
        onClose();
      }
      return;
    }
    onSaveProducts(localList);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-96">
        <h3 className="text-xl mb-4">Low-Stock Products</h3>
        <ul className="space-y-2 mb-4 max-h-60 overflow-y-auto">
          {localList.map((p) => (
            <li key={p._id} className="flex justify-between items-center">
              <span className="truncate">{p.description || p._id}</span>
              <input
                type="number"
                min={0}
                value={p.displayedStock}
                onChange={(e) => handleChange(p._id, e.target.value)}
                className="w-20 border rounded px-2 py-1"
              />
            </li>
          ))}
        </ul>
        <div className="flex justify-end space-x-2">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-300 hover:bg-gray-400 rounded"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-blue-600 text-white rounded"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
};

// Notification bell
const NotificationBell = React.memo(({ products, onSaveProducts }) => {
  const lowStock = useMemo(
    () => products.filter((p) => p.displayedStock <= (p.threshold ?? 3)),
    [products]
  );
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(true)}
        className="relative focus:outline-none"
      >
        <svg
          className="w-8 h-8 text-gray-700"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 17h5l-1.405-1.405A2.032…"
          />
        </svg>
        {lowStock.length > 0 && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold text-red-100 bg-red-600 rounded-full">
            {lowStock.length}
          </span>
        )}
      </button>
      {isOpen && (
        <LowStockModal
          lowStockProducts={lowStock}
          onClose={() => setIsOpen(false)}
          onSaveProducts={onSaveProducts}
        />
      )}
    </div>
  );
});

// Orders management modal
const OrdersModal = ({ orders, onClose, onStatusChange }) => {
  const [expandedId, setExpandedId] = useState(null);
  const [expandedData, setExpandedData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [productMap, setProductMap] = useState({});

  useEffect(() => {
    axios
      .get(`${API_URL}/products`)
      .then((res) => {
        const map = {};
        res.data.forEach((p) => (map[p._id] = p.description));
        setProductMap(map);
      })
      .catch((err) => console.error("Error loading products:", err));
  }, []);

  const toggleExpand = async (id) => {
    if (expandedId === id) {
      setExpandedId(null);
      setExpandedData(null);
      return;
    }
    setExpandedId(id);
    setLoading(true);
    try {
      const res = await axios.get(
        `${API_URL}/successOrder/single/${id}`,
        { headers: getAuthHeaders() }
      );
      setExpandedData(res.data);
    } catch {
      setExpandedData(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50"
      onClick={onClose}
    >
      <div
        className="bg-white p-6 rounded-lg w-11/12 md:w-3/4 lg:w-1/2 max-h-[80vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-bold">Manage Orders</h3>
          <button onClick={onClose} className="text-gray-500 text-2xl">
            &times;
          </button>
        </div>
        <table className="min-w-full border border-gray-300">
          <thead className="bg-gray-100">
            <tr>

     
              <th className="border p-2">Created At</th>
              <th className="border p-2">Total Amount</th>
              <th className="border p-2">Quantity</th>
              <th className="border p-2">Order Status</th>
              <th className="border p-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {orders.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center p-4">
                  No orders
                </td>
              </tr>
            ) : (
              orders.map((o) => {
                const qty = (o.items || []).reduce(
                  (sum, i) => sum + (i.quantity || 0),
                  0
                );
                return (
                  <React.Fragment key={o._id}>
                    <tr
                      className={`hover:bg-gray-50 ${
                        o.actionTaken === "completed"
                          ? "bg-green-300"
                          : o.actionTaken === "failed"
                          ? "bg-red-300 line-through"
                          : ""
                      }`}
                    >

                      <td className="border p-2">
                        {new Date(o.createdAt).toLocaleString()}
                      </td>
                      <td className="border p-2">{o.totalAmount}</td>
                      <td className="border p-2">{qty}</td>
                      <td className="border p-2">{o.status}</td>
                      <td className="border p-2 flex flex-col items-center space-y-2">
                        <button
                          onClick={() => onStatusChange(o._id, "Completed")}
                          className="px-2 py-1 bg-green-500 text-white rounded w-32"
                        >
                          {o.actionTaken === "completed"
                            ? "Undo Order Done"
                            : "Order Done"}
                        </button>
                        <button
                          onClick={() => onStatusChange(o._id, "Failed")}
                          className="px-2 py-1 bg-red-500 text-white rounded w-32"
                        >
                          Mark as Failed
                        </button>
                        <button
                          onClick={() => toggleExpand(o._id)}
                          className="px-2 py-1 bg-blue-500 text-white rounded w-32"
                        >
                          {expandedId === o._id ? "Hide Order" : "View Order"}
                        </button>
                      </td>
                    </tr>
                    {expandedId === o._id && (
                      <tr>
                        <td colSpan={7} className="p-4 bg-gray-700 text-white">
                          {loading
                            ? "Loading details..."
                            : expandedData ? (
                                <div>
                                  <h4 className="underline">
                                    Customer Details
                                  </h4>
                                  <p>
                                    <strong>Name:</strong>{" "}
                                    {expandedData.successOrder.customerId
                                      ?.name || "-"}
                                  </p>
                                  <p>
                                    <strong>Phone:</strong>{" "}
                                    {expandedData.relatedOrder?.phoneNo || "-"}
                                  </p>
                                  <p>
                                    <strong>Email:</strong>{" "}
                                    {expandedData.successOrder.customerId
                                      ?.email || "-"}
                                  </p>
                                  <h4 className="mt-4 underline">Order Items</h4>
                                  <ul className="list-disc pl-6">
                                    {expandedData.successOrder.items.map(
                                      (it, idx) => (
                                        <li key={idx}>
                                          {it.itemType === "Product" ? (
                                            <>
                                              Product ID: {it.itemId} —{" "}
                                              {productMap[it.itemId] ||
                                                "N/A"}
                                            </>
                                          ) : (
                                            <>
                                              PreBuild Specs:
                                              <ul className="pl-4 list-disc">
                                                {it.specs.map((s, j) => (
                                                  <li key={j}>
                                                    {s._id} — {s.label}:{" "}
                                                    {s.value}
                                                  </li>
                                                ))}
                                              </ul>
                                            </>
                                          )}
                                        </li>
                                      )
                                    )}
                                  </ul>
                                </div>
                              ) : (
                                "No details found."
                              )}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
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

  const handleGenerateCSV = () => {
    const headers = ["Description", "Price", "Discount", "Discount Price", "Threshold", "Stock", "Availability"];
    const rows = filtered.map(p => [

      p.description,
      p.price,
      p.discount || 0,
      p.discountPrice != null
        ? p.discountPrice
        : (p.price - (p.price * (p.discount || 0)) / 100).toFixed(2),
      p.threshold,
      p.displayedStock,
      p.availability
    ]);
  
    const csvContent =
      "data:text/csv;charset=utf-8," +
      [headers, ...rows].map(e => e.join(",")).join("\n");
  
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `inventory_report_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };
  
  const handleGeneratePDF = () => {
    const doc = new jsPDF("p", "mm", "a4");
    const pageWidth = doc.internal.pageSize.getWidth();
    const now = new Date();
    const dateStr = now.toLocaleDateString();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  
    const logoUrl = `${window.location.origin}/Logo.jpg`;
  
    new Promise((resolve) => {
      const img = new Image();
      img.crossOrigin = "Anonymous";
      img.onload = () => {
        const logoWidth = 35;
        const logoHeight = logoWidth * (img.height / img.width);
        doc.addImage(img, "JPEG", 15, 10, logoWidth, logoHeight);
        resolve();
      };
      img.src = logoUrl;
    }).then(() => {
      // Theme colors
      const primaryColor = "#2c3e50";  // Dark Blue
      const secondaryColor = "#7f8c8d"; // Gray
      const accentColor = "#10b981";    // Emerald Green
      const lightColor = "#F9FAFB";     // Light background
  
      doc.setFont("helvetica");
  
      // Company Info
      doc.setFontSize(10);
      doc.setTextColor(secondaryColor);
      doc.text("Alpha IT Solutions", 180, 15, { align: "right" });
      doc.text("26/C/3 Biyagama Road, Talwatta", 180, 20, { align: "right" });
      doc.text("Gonawala, Kelaniya 11600", 180, 25, { align: "right" });
      doc.text("Tel: 077 625 2822", 180, 30, { align: "right" });
  
      // Main Topic
      doc.setFontSize(22);
      doc.setTextColor(primaryColor);
      doc.setFont(undefined, "bold");
      doc.text("Inventory & Sales Report", pageWidth / 2, 50, { align: "center" });
  
      // Subtext - Date and Time
      doc.setFontSize(12);
      doc.setTextColor(secondaryColor);
      doc.text(`Date: ${dateStr} | Time: ${timeStr}`, pageWidth / 2, 58, { align: "center" });
  
      // Horizontal Line
      doc.setDrawColor(primaryColor);
      doc.setLineWidth(0.3);
      doc.line(15, 63, 195, 63);
  
      // Table Data
      const columns = [
        "Description", "Price", "Discount %", "Discount Price", "Threshold", "Stock", "Availability"
      ];
      const rows = filtered.map((p) => [
        p.description,
        p.price,
        p.discount || 0,
        p.discountPrice != null
          ? p.discountPrice
          : (p.price - (p.price * (p.discount || 0)) / 100).toFixed(2),
        p.threshold,
        p.displayedStock,
        p.availability,
      ]);
  
      doc.autoTable({
        startY: 70,
        head: [columns],
        body: rows,
        theme: "striped",
        headStyles: { fillColor: accentColor, textColor: 255 },
        styles: { fontSize: 8, cellPadding: 2 },
        margin: { left: 10, right: 10 },
        didDrawPage: (data) => {
          // Redraw header if multiple pages
          if (data.pageNumber > 1) {
            doc.setFontSize(22);
            doc.setTextColor(primaryColor);
            doc.setFont(undefined, "bold");
            doc.text("Inventory & Sales Report", pageWidth / 2, 20, { align: "center" });
  
            doc.setFontSize(12);
            doc.setTextColor(secondaryColor);
            doc.setFont(undefined, "normal");
            doc.text(`Date: ${dateStr} | Time: ${timeStr}`, pageWidth / 2, 28, { align: "center" });
  
            doc.setDrawColor(primaryColor);
            doc.setLineWidth(0.3);
            doc.line(15, 33, 195, 33);
          }
  
          // Footer
          const pageHeight = doc.internal.pageSize.height;
          doc.setFontSize(8);
          doc.setTextColor("#999999");
          doc.text(
            `Generated by Alpha IT Solutions - Page ${data.pageNumber}`,
            pageWidth / 2,
            pageHeight - 10,
            { align: "center" }
          );
        }
      });
  
      // Border
      doc.setDrawColor(lightColor);
      doc.setLineWidth(0.5);
      doc.rect(5, 5, 200, 287);
  
      doc.save(`inventory_report_${now.toISOString().slice(0, 10)}.pdf`);
    }).catch((error) => {
      console.error("PDF Generation Failed:", error);
      alert("Failed to generate PDF. Please try again.");
    });
  };
  
  
  
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
          availability: p.availability || "in stock",
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

  // Adjust stock helper
  const adjustStockForOrder = (order, factor) => {
    const adj = {};
    const specsSet = new Set();
    (order.items || []).forEach((it) => {
      if (it.itemType === "Product") {
        const id = it.itemId._id || it.itemId;
        adj[id] = (adj[id] || 0) + factor * (it.quantity || 1);
      } else {
        (it.specs || []).forEach((s) => s._id && specsSet.add(s._id));
      }
    });
    specsSet.forEach((id) => {
      adj[id] = (adj[id] || 0) + factor;
    });
    Object.entries(adj).forEach(([id, qty]) =>
      updateProductStock(id, qty)
    );
  };

  // Update product stock on server & state
  const updateProductStock = (productId, change) => {
    setProducts((prev) =>
      prev.map((p) => {
        if (p._id !== productId) return p;
        const newStock = Math.max(0, p.displayedStock + change);
        axios
          .patch(
            `${API_URL}/products/${productId}/inventory`,
            { displayedStock: newStock },
            { headers: getAuthHeaders() }
          )
          .catch((err) => console.error(err));
        return { ...p, displayedStock: newStock };
      })
    );
  };

  // Load orders and handle initial adjustments
  useEffect(() => {
    if (!showOrdersModal) return;
    axios
      .get(`${API_URL}/successOrder/admin/all`, {
        headers: getAuthHeaders(),
      })
      .then((res) => {
        const raw = Array.isArray(res.data) ? res.data : res.data.orders;
        const persisted = loadStatusMap();
        const toAdjust = [];
        const enriched = raw.map((o) => {
          const serverStatus = o.status.toLowerCase();
          let actionTaken =
            persisted[o._id]?.toLowerCase() ||
            (["approved", "handedOver"].includes(serverStatus)
              ? "completed"
              : serverStatus === "cancelled"
              ? "failed"
              : null);
          if (!persisted[o._id] && actionTaken === "completed") {
            toAdjust.push(o);
            persisted[o._id] = "Completed";
          }
          return { ...o, actionTaken, status: o.status };
        });
        setOrders(enriched);
        saveStatusMap(persisted);
        toAdjust.forEach((o) => adjustStockForOrder(o, -1));
      })
      .catch(() => setOrders([]));
  }, [showOrdersModal]);

  // Handle manual status change
  const handleStatusChange = (orderId, newStatus) => {
    const oldOrder = orders.find((o) => o._id === orderId);
    const prev = oldOrder.actionTaken;
    let factor = 0;
    if (newStatus === "Completed") factor = prev !== "completed" ? -1 : +1;
    if (newStatus === "Failed" && prev === "completed") factor = +1;
    if (factor) adjustStockForOrder(oldOrder, factor);

    const updated = orders.map((o) => {
      if (o._id !== orderId) return o;
      let at = o.actionTaken;
      if (newStatus === "Completed") at = prev === "completed" ? null : "completed";
      else if (newStatus === "Failed") at = prev === "failed" ? null : "failed";
      return { ...o, actionTaken: at, status: at ? at[0].toUpperCase() + at.slice(1) : o.status };
    });
    setOrders(updated);
    const map = loadStatusMap();
    const cur = updated.find((o) => o._id === orderId);
    if (cur.actionTaken) map[orderId] = cur.status;
    else delete map[orderId];
    saveStatusMap(map);
  };

  // Save low-stock modal changes
  const handleSaveProducts = useCallback(async (updatedOnes) => {
    setProducts((prev) =>
      prev.map((p) => {
        const u = updatedOnes.find((x) => x._id === p._id);
        return u
          ? { ...p, displayedStock: u.displayedStock, availability: u.availability || p.availability }
          : p;
      })
    );
    await Promise.all(
      updatedOnes.map((p) =>
        axios.patch(
          `${API_URL}/products/${p._id}/inventory`,
          { displayedStock: p.displayedStock, availability: p.availability },
          { headers: getAuthHeaders() }
        )
      )
    );
  }, []);

  // Mark out of stock
  const handleMarkOutOfStock = async (productId) => {
    try {
      await axios.patch(
        `${API_URL}/products/${productId}/inventory`,
        { displayedStock: 0, availability: "out of stock" },
        { headers: getAuthHeaders() }
      );
      setProducts((prev) =>
        prev.map((p) =>
          p._id === productId
            ? { ...p, displayedStock: 0, availability: "out of stock" }
            : p
        )
      );
    } catch {
      alert("Could not mark product as out of stock.");
    }
  };

  // Filtering
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
          <NotificationBell products={products} onSaveProducts={handleSaveProducts} />
        </div>
      </div>

      {/* Orders Modal */}
      {showOrdersModal && (
        <OrdersModal orders={orders} onClose={() => setShowOrdersModal(false)} onStatusChange={handleStatusChange} />
      )}

     {/* Search & Filter Row */}
<div className="flex justify-between items-center mb-4">
  <input
    type="text"
    placeholder="Search products…"
    value={searchQuery}
    onChange={(e) => setSearchQuery(e.target.value)}
    className="w-1/2 p-2 border rounded"
  />
  <select
    value={filterCategory}
    onChange={(e) => setFilterCategory(e.target.value)}
    className="w-1/4 p-2 border rounded"
  >
    <option value="">All Categories</option>
    {[...new Set(products.map((p) => p.category))].map((cat) => (
      <option key={cat} value={cat}>
        {cat}
      </option>
    ))}
  </select>
</div>

{/* CSV / PDF Button Row */}
<div className="flex space-x-4 mb-6">
  <button
    onClick={handleGenerateCSV}
    className="px-4 py-2 bg-green-600 text-white rounded"
  >
    Generate CSV
  </button>

  <button
    onClick={handleGeneratePDF}
    className="px-4 py-2 bg-blue-600 text-white rounded"
  >
    Generate PDF
  </button>
</div>



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
              <th className="p-2 border">Description</th>
              <th className="p-2 border">Price</th>
              <th className="p-2 border">Discount %</th>
              <th className="p-2 border">Discount Price</th>
              <th className="p-2 border">Threshold</th>
              <th className="p-2 border">Stock</th>
              <th className="p-2 border">Availability</th>
              <th className="p-2 border">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((p) => {
              const discPrice =
                p.discountPrice != null
                  ? p.discountPrice
                  : (p.price - (p.price * (p.discount || 0)) / 100).toFixed(2);
              return (
                <tr
                  key={p._id}
                  className={`hover:bg-gray-50 ${
                    p.displayedStock <= p.threshold ? "bg-red-100" : ""
                  } ${p.displayedStock <= 0 ? "bg-yellow-300" : ""}`}
                >
                  <td className="p-2 border">{p.description}</td>
                  <td className="p-2 border">{p.price}</td>
                  <td className="p-2 border">{p.discount || 0}</td>
                  <td className="p-2 border">{discPrice}</td>
                  <td className="p-2 border">{p.threshold}</td>
                  <td className="p-2 border">{p.displayedStock}</td>
                  <td className="p-2 border">{p.availability}</td>
                  <td className="p-2 border space-y-2">
                    {p.displayedStock <= 0 ? (
                      <>
                        <button
                          onClick={() => handleMarkOutOfStock(p._id)}
                          className="w-full py-1 bg-red-600 text-white rounded"
                        >
                          Mark Out of Stock
                        </button>
                        <button
                          onClick={() => setSelectedProduct(p)}
                          className="w-full py-1 bg-blue-600 text-white rounded"
                        >
                          Edit Stock
                        </button>
                      </>
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
              );
            })}
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

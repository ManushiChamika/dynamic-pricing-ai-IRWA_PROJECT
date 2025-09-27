// src/components/ProductSpecsSalesReport.jsx
import React, { useEffect, useState } from "react";
import axios from "axios";
import jsPDF from "jspdf";
import "jspdf-autotable";
import { subDays, format } from "date-fns";

const getAuthHeaders = () => {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export default function ProductSpecsSalesReport() {
  const [products, setProducts] = useState([]);
  const [orders, setOrders]       = useState([]);

  useEffect(() => {
    // Fetch products
    axios.get("/api/products")
      .then(res => setProducts(res.data))
      .catch(console.error);

    // Fetch orders
    axios.get("/api/successOrder/admin/all", { headers: getAuthHeaders() })
      .then(res => {
        const data = Array.isArray(res.data) ? res.data : res.data.orders;
        setOrders(data);
      })
      .catch(console.error);
  }, []);

  const handleDownloadReport = () => {
    const doc = new jsPDF("p", "pt", "a4");
    const today = format(new Date(), "yyyy-MM-dd HH:mm");

    // --- Cover Page ---
    doc.setFontSize(24);
    doc.text("Product & Sales Summary Report", 40, 80);
    doc.setFontSize(12);
    doc.text(`Generated: ${today}`, 40, 110);
    doc.addPage();

    // --- 1. Product Catalog ---
    doc.setFontSize(18);
    doc.text("1. Product Catalog", 40, 40);
    const catalogBody = products.map(p => [
      p._id,
      p.description,
      p.category,
      // join specs: "key:value; key2:value2"
      (Array.isArray(p.specs) ? 
        p.specs.map(s => `${s.key}:${s.value}`).join("; ")
        : ""),
      `₨ ${p.price.toLocaleString()}`
    ]);
    doc.autoTable({
      startY: 60,
      head: [["ID", "Name", "Category", "Specs", "Price"]],
      body: catalogBody,
      styles: { fontSize: 8 },
      headStyles: { fillColor: "#346751" },
      columnStyles: { 3: { cellWidth: 120 } }, // specs column
      margin: { left: 40, right: 40 }
    });
    doc.addPage();

    // --- 2. Inventory Status ---
    doc.setFontSize(18);
    doc.text("2. Inventory Status", 40, 40);
    const invBody = products.map(p => {
      const stock = p.displayedStock ?? 0;
      const th    = p.threshold ?? 0;
      return [
        p._id,
        p.description,
        stock,
        th,
        stock <= th ? "Yes" : "No"
      ];
    });
    doc.autoTable({
      startY: 60,
      head: [["ID", "Product", "On-Hand", "Threshold", "Reorder?"]],
      body: invBody,
      styles: { fontSize: 9 },
      headStyles: { fillColor: "#fb8500" },
      margin: { left: 40, right: 40 }
    });
    doc.addPage();

    // --- 3. Sales Trends (last 14 days) ---
    doc.setFontSize(18);
    doc.text("3. Sales Trends (Last 14 Days)", 40, 40);

    // aggregate orders per day
    const dayMap = {};
    for (let i = 14; i >= 1; i--) {
      const d = subDays(new Date(), i);
      const key = format(d, "yyyy-MM-dd");
      dayMap[key] = 0;
    }
    orders.forEach(o => {
      const key = format(new Date(o.createdAt), "yyyy-MM-dd");
      if (dayMap[key] != null) {
        dayMap[key] += o.totalAmount;
      }
    });
    const trendBody = Object.entries(dayMap).map(([day, amt]) => [
      format(new Date(day), "MMM dd"),
      `₨ ${amt.toLocaleString()}`
    ]);
    doc.autoTable({
      startY: 60,
      head: [["Date", "Total Sales"]],
      body: trendBody,
      styles: { fontSize: 10 },
      headStyles: { fillColor: "#2a9d8f" },
      margin: { left: 40, right: 40 }
    });
    doc.addPage();

    // --- 4. Highlights ---
    doc.setFontSize(18);
    doc.text("4. Highlights", 40, 40);

    // Top 5 bestsellers
    const soldMap = {};
    orders.forEach(o =>
      (o.items || []).forEach(it => {
        if (it.itemType === "Product") {
          const id = typeof it.itemId === "object" ? it.itemId._id : it.itemId;
          soldMap[id] = (soldMap[id] || 0) + (it.quantity || 1);
        }
      })
    );
    const sellers = products.map(p => ({
      name: p.description,
      sold: soldMap[p._id] || 0
    }));
    sellers.sort((a,b) => b.sold - a.sold);
    const top5 = sellers.slice(0,5).map(s => [s.name, s.sold]);

    doc.setFontSize(14);
    doc.text("Top 5 Bestselling Products", 40, 80);
    doc.autoTable({
      startY: 100,
      head: [["Product", "Units Sold"]],
      body: top5,
      styles: { fontSize: 10 },
      headStyles: { fillColor: "#e63946" },
      margin: { left: 40, right: 40 }
    });

    // footer on every page
    const pageCount = doc.internal.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      doc.setPage(i);
      doc.setFontSize(8);
      doc.text(`Page ${i} of ${pageCount}`,  doc.internal.pageSize.getWidth()/2, doc.internal.pageSize.getHeight() - 20, { align: "center" });
    }

    doc.save(`Full_Product_Sales_Inventory_Report_${format(new Date(), "yyyy-MM-dd")}.pdf`);
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <h1 className="text-3xl font-bold mb-6 text-center">
        Full Product & Sales-Inventory Report
      </h1>
      <div className="flex justify-center">
        <button
          onClick={handleDownloadReport}
          className="px-6 py-3 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
        >
          📄 Download Full Report PDF
        </button>
      </div>
    </div>
  );
}

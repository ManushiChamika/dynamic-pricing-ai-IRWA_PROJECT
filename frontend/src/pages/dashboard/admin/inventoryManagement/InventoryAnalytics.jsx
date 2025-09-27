import React, { useEffect, useState, useMemo, useRef } from "react";
import axios from "axios";
import { Bar, Line, Pie } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  Filler
} from "chart.js";
import jsPDF from "jspdf";
import "jspdf-autotable";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const computePieData = (products) => {
  let inStock = 0,
    low = 0,
    out = 0;
  products.forEach((p) => {
    if (p.displayedStock <= 0) out++;
    else if (p.displayedStock <= p.threshold) low++;
    else inStock++;
  });
  return { InStock: inStock, LowStock: low, OutOfStock: out };
};

const aggregateOrders = (orders) => {
  const perProduct = {};
  const perDay = {};
  orders.forEach((o) => {
    const day = new Date(o.createdAt).toISOString().slice(0, 10);
    perDay[day] = (perDay[day] || 0) + o.totalAmount;
    o.items?.forEach((it) => {
      if (it.itemType !== "Product") return;
      const id =
        typeof it.itemId === "object" ? it.itemId._id : it.itemId;
      if (!perProduct[id]) perProduct[id] = { sold: 0, revenue: 0 };
      perProduct[id].sold += it.quantity || 0;
      perProduct[id].revenue +=
        (it.priceAtSale || 0) * (it.quantity || 0);
    });
  });
  return { perProduct, perDay };
};

export default function InventoryAnalytics() {
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const pieRef = useRef();
  const barRef = useRef();
  const lineRef = useRef();

  useEffect(() => {
    (async () => {
      try {
        const [prodRes, ordRes] = await Promise.all([
          axios.get("http://localhost:5000/api/products"),
          axios.get("http://localhost:5000/api/successOrder/admin/all", {
            headers: {
              Authorization: `Bearer ${localStorage.getItem("token")}`
            }
          })
        ]);
        setProducts(
          prodRes.data.map((p) => ({
            ...p,
            displayedStock: p.displayedStock ?? 0,
            threshold: p.threshold ?? 3
          }))
        );
        setOrders(
          Array.isArray(ordRes.data) ? ordRes.data : ordRes.data.orders
        );
      } catch (err) {
        console.error("Analytics fetch error:", err);
      }
    })();
  }, []);

  const { pieData, barData, lineData, topSellers, lowStock, topRevenue } =
    useMemo(() => {
      const pieCounts = computePieData(products);
      const { perProduct, perDay } = aggregateOrders(orders);

      const bars = products
        .map((p) => ({
          label: p.description?.slice(0, 20) || p._id,
          inStock: p.displayedStock,
          sold: perProduct[p._id]?.sold || 0,
          revenue: perProduct[p._id]?.revenue || 0
        }))
        .filter((r) => r.inStock > 0 || r.sold > 0);

      const topSellers = [...bars]
        .sort((a, b) => b.sold - a.sold)
        .slice(0, 5);
      const lowStock = [...bars]
        .sort((a, b) => a.inStock - b.inStock)
        .slice(0, 5);
      const topRevenue = [...bars]
        .sort((a, b) => b.revenue - a.revenue)
        .slice(0, 5);

      const today = new Date();
      const line = [...Array(30)].map((_, i) => {
        const d = new Date(today);
        d.setDate(d.getDate() - (29 - i));
        const key = d.toISOString().slice(0, 10);
        return { date: key.slice(5), revenue: perDay[key] || 0 };
      });

      return {
        pieData: pieCounts,
        barData: bars,
        lineData: line,
        topSellers,
        lowStock,
        topRevenue
      };
    }, [products, orders]);

  const pieChartData = {
    labels: ["In Stock", "Low Stock", "Out of Stock"],
    datasets: [
      {
        label: "Stock Status",
        data: Object.values(pieData),
        backgroundColor: ["#4ade80", "#facc15", "#f87171"]
      }
    ]
  };
  const barChartData = {
    labels: barData.map((x) => x.label),
    datasets: [
      {
        label: "In Stock",
        data: barData.map((x) => x.inStock),
        backgroundColor: "rgba(96, 165, 250, 0.7)"
      },
      {
        label: "Sold",
        data: barData.map((x) => x.sold),
        backgroundColor: "rgba(248, 113, 113, 0.7)"
      }
    ]
  };
  const lineChartData = {
    labels: lineData.map((x) => x.date),
    datasets: [
      {
        label: "Revenue (Last 30 Days)",
        data: lineData.map((x) => x.revenue),
        borderColor: "#10b981",
        backgroundColor: "rgba(16, 185, 129, 0.2)",
        fill: true,
        tension: 0.4
      }
    ]
  };

 // [No other part changed; below is just the updated `handleGenerateReport` function]

const handleGenerateReport = async () => {
  const doc = new jsPDF("p", "mm", "a4");
   // Colors
   const primaryColor = "#2c3e50";
   const secondaryColor = "#7f8c8d";
   const accentColor = "#10b981";
 
   // Load Logo
   const logoUrl = `${window.location.origin}/Logo.jpg`;
   await new Promise((resolve, reject) => {
     const img = new Image();
     img.crossOrigin = "anonymous";
     img.onload = () => {
       doc.addImage(img, "JPEG", 10, 10, 20, 20);
       resolve();
     };
     img.onerror = reject;
     img.src = logoUrl;
   });
 
   // Company Info
   doc.setFont("helvetica", "normal");
   doc.setFontSize(10);
   doc.setTextColor(secondaryColor);
   const companyInfo = [
     "Alpha IT Solutions",
     "26/C/3 Biyagama Road, Talwatta",
     "Kelaniya 11600",
     "Tel: 077 625 2822"
   ];
   companyInfo.forEach((line, idx) => {
     doc.text(line, 190, 12 + idx * 5, { align: "right" });
   });
 
   // Document Title
   doc.setFontSize(18);
   doc.setTextColor(accentColor);
   doc.setFont(undefined, "bold");
   doc.text("Inventory & Sales Report", 105, 45, { align: "center" });
 
   // Generated On
   doc.setFontSize(10);
   doc.setFont(undefined, "normal");
   doc.setTextColor(primaryColor);
   doc.text(`Generated on: ${new Date().toLocaleString()}`, 10, 55);
 
   const addFooter = () => {
     doc.setFontSize(8);
     doc.setTextColor("#999999");
     doc.text("Generated by Alpha IT Solutions | Confidential", 105, 290, { align: "center" });
   };
 

  // Group products by category
  const byCat = products.reduce((acc, p) => {
    acc[p.category] = acc[p.category] || [];
    acc[p.category].push(p);
    return acc;
  }, {});

  // Product tables without specs
  Object.entries(byCat).forEach(([category, prods], idx) => {
    if (idx > 0) doc.addPage();

    const columns = ["_id", "price", "discountPrice", "displayedStock", "state", "availability"];

    const body = prods.map((p) => ([
      p._id,
      p.price,
      p.discountPrice ?? "",
      p.displayedStock,
      p.state,
      p.availability
    ]));

    doc
      .setFontSize(16)
      .setTextColor(accentColor)
      .setFont(undefined, "bold")
      .text(`${category.toUpperCase()} Products`, 105, 20, { align: "center" });

    doc.autoTable({
      startY: 30,
      head: [columns],
      body,
      theme: "grid",
      headStyles: { fillColor: accentColor },
      styles: { fontSize: 8, cellPadding: 2 },
      margin: { left: 10, right: 10 }
    });

    addFooter();
  });

  // Summary Tables page
  doc.addPage();
  doc
    .setFontSize(16)
    .setTextColor(accentColor)
    .setFont(undefined, "bold")
    .text("Summary Tables", 105, 20, { align: "center" });

  // Stock summary
  const pieCounts = computePieData(products);
  const stockRows = [
    ["In Stock", pieCounts.InStock],
    ["Low Stock", pieCounts.LowStock],
    ["Out of Stock", pieCounts.OutOfStock]
  ];

  doc
    .setFontSize(14)
    .setTextColor(primaryColor)
    .setFont(undefined, "normal")
    .text("Stock Summary", 15, 30);

  doc.autoTable({
    startY: 35,
    head: [["Status", "Count"]],
    body: stockRows,
    theme: "striped",
    headStyles: { fillColor: accentColor },
    styles: { fontSize: 10 },
    margin: { left: 15, right: 15 }
  });

  // Revenue last 7 days
  const { perDay } = aggregateOrders(orders);
  const last7 = Object.keys(perDay)
    .sort()
    .slice(-7)
    .map((date) => [date, perDay[date].toLocaleString()]);

  doc
    .setFontSize(14)
    .text("Revenue (Last 7 Days)", 15, doc.lastAutoTable.finalY + 15);

  doc.autoTable({
    startY: doc.lastAutoTable.finalY + 20,
    head: [["Date", "Revenue (LKR)"]],
    body: last7,
    theme: "striped",
    headStyles: { fillColor: accentColor },
    styles: { fontSize: 10 },
    margin: { left: 15, right: 15 }
  });

  addFooter();

  doc.save(`Inventory_Analytics_Report_${new Date().toISOString().slice(0, 10)}.pdf`);
};


  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      {/* Title */}
      <h3 className="text-4xl font-extrabold mb-10 text-gray-800 uppercase tracking-wide text-center">
        📦 Inventory & Sales Analytics
      </h3>

      {/* Generate Report Button */}
      <div className="flex justify-center mb-12">
        <button
          onClick={handleGenerateReport}
          className="px-8 py-4 bg-green-600 hover:bg-green-700 text-white font-bold rounded-lg shadow-lg text-lg transition duration-300"
        >

        </button>
      </div>

      {/* All Charts */}
      <div className="space-y-16 bg-white rounded-3xl shadow-2xl p-10">
        {/* Stock Distribution */}
        <div
          ref={pieRef}
          style={{ background: "#ffffff" }}
          className="flex flex-col items-center space-y-6 rounded-2xl shadow p-4"
        >
          <h4 className="text-2xl font-bold text-gray-700">
            Stock Distribution
          </h4>
          <div className="w-[400px] h-[400px]">
            <Pie
              data={pieChartData}
              options={{ responsive: false, maintainAspectRatio: false }}
              width={400}
              height={400}
            />
          </div>
        </div>

        {/* Stock vs Sold */}
        <div
          ref={barRef}
          style={{ background: "#ffffff" }}
          className="h-[500px] rounded-2xl shadow p-4"
        >
          <h4 className="text-2xl font-bold mb-6 text-center text-gray-700">
            Stock vs Sold
          </h4>
          <Bar
            data={barChartData}
            options={{ responsive: true, maintainAspectRatio: false }}
          />
        </div>

        {/* Revenue Trend */}
        <div
          ref={lineRef}
          style={{ background: "#ffffff" }}
          className="h-[500px] rounded-2xl shadow p-4"
        >
          <h4 className="text-2xl font-bold mb-6 text-center text-gray-700">
            Revenue Trend (Last 30 Days)
          </h4>
          <Line
            data={lineChartData}
            options={{ responsive: true, maintainAspectRatio: false }}
          />
        </div>

        {/* Highlights Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
          {/* Top 5 Bestselling */}
          <div
            className="h-[500px] rounded-xl p-6 shadow-lg flex flex-col"
            style={{ background: "#ffffff" }}
          >
            <h4 className="text-2xl font-bold mb-4 text-center text-blue-600">
              🥇 Top 5 Bestselling Products
            </h4>
            <Bar
              data={{
                labels: topSellers.map((x) => x.label),
                datasets: [
                  {
                    label: "Units Sold",
                    data: topSellers.map((x) => x.sold),
                    backgroundColor: "rgba(59, 130, 246, 0.7)"
                  }
                ]
              }}
              options={{ responsive: true, maintainAspectRatio: false }}
            />
          </div>

          {/* Top 5 Low Stock */}
          <div
            className="h-[500px] rounded-xl p-6 shadow-lg flex flex-col"
            style={{ background: "#ffffff" }}
          >
            <h4 className="text-2xl font-bold mb-4 text-center text-yellow-600">
              ⚠️ Top 5 Low Stock Products
            </h4>
            <Bar
              data={{
                labels: lowStock.map((x) => x.label),
                datasets: [
                  {
                    label: "Stock Remaining",
                    data: lowStock.map((x) => x.inStock),
                    backgroundColor: "rgba(250, 204, 21, 0.7)"
                  }
                ]
              }}
              options={{ responsive: true, maintainAspectRatio: false }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

// src/components/ProductCategoryAnalytics.jsx
import React, { useEffect, useState, useMemo, useRef } from "react";
import axios from "axios";
import { Bar } from "react-chartjs-2";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function ProductCategoryAnalytics() {
  const [products, setProducts] = useState([]);
  const chartRef = useRef(null);

  useEffect(() => {
    axios
      .get("http://localhost:5000/api/products")
      .then(res => setProducts(res.data))
      .catch(err => console.error("Error fetching products:", err));
  }, []);

  const categoryData = useMemo(() => {
    const counts = {};
    products.forEach(p => {
      const cat = p.category || "Uncategorized";
      counts[cat] = (counts[cat] || 0) + 1;
    });
    return counts;
  }, [products]);

  const barData = {
    labels: Object.keys(categoryData),
    datasets: [
      {
        label: "Number of Products",
        data: Object.values(categoryData),
        backgroundColor: "rgba(96, 165, 250, 0.7)"
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      title: {
        display: true,
        text: "Product Distribution by Category",
        font: { size: 24 }
      },
      legend: { display: false }
    },
    scales: {
      y: { beginAtZero: true }
    }
  };

  const downloadPNG = () => {
    if (!chartRef.current) return;
    const url = chartRef.current.toBase64Image();
    const link = document.createElement("a");
    link.href = url;
    link.download = "product-category-distribution.png";
    link.click();
  };

  const downloadPDF = async () => {
    if (!chartRef.current) return;
    // Render the chart container to canvas
    const canvas = await html2canvas(chartRef.current.canvas, { scale: 2 });
    const imgData = canvas.toDataURL("image/png");
    // Create PDF
    const pdf = new jsPDF("p", "pt", "a4");
    const pageWidth = pdf.internal.pageSize.getWidth();
    const imgProps = pdf.getImageProperties(imgData);
    const imgHeight = (imgProps.height * pageWidth) / imgProps.width;
    pdf.addImage(imgData, "PNG", 0, 0, pageWidth, imgHeight);
    pdf.save("product-category-distribution.pdf");
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <h3 className="text-4xl font-extrabold mb-6 text-gray-800 uppercase tracking-wide text-center">
        📚 Product Categories Overview
      </h3>

      {/* Buttons go here */}
      <div className="flex justify-end space-x-4 mb-4">
        <button
          onClick={downloadPNG}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
        >
          Download PNG
        </button>
        <button
          onClick={downloadPDF}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition"
        >
          Download PDF
        </button>
      </div>

      <div className="bg-white rounded-3xl shadow-2xl p-10 h-[600px]">
        {products.length > 0 ? (
          <Bar ref={chartRef} data={barData} options={options} />
        ) : (
          <p className="text-center text-lg text-gray-500">Loading products...</p>
        )}
      </div>
    </div>
  );
}

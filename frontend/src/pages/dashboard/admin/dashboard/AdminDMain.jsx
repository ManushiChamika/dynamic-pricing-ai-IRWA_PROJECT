import React, { useState } from "react";
import InquiryChart from "../../../../components/InquiryChart/InquiryChart";
import ReviewChart from "../../../../components/ReviewChart/ReviewChart";
import AppointmentAnalytics from "../charts/AppointmentChart";
import OrderChart from "../../../../components/orderChart/orderChart";
import OrderSuccessDashboard from "../../../../components/orderChart/OrderSuccessDashboard";
import TransactionDashboard from "../charts/TransactionDashboard";
import InventoryAnalytics from "../inventoryManagement/InventoryAnalytics";
import PreBuildAnalytics from "../../../../components/CustomBuilds/PreBuildAnalytics";

const Dashboard = () => {
  const [activeChart, setActiveChart] = useState(null);

  const handleChartClick = (chartName) => {
    setActiveChart(chartName === activeChart ? null : chartName);
  };

  return (
    <div style={dashboardContainer}>
      <main style={mainContent}>
        <section style={chartListSection}>
        <button
            style={{
              ...chartButton,
              ...(activeChart === "inventory" ? activeButtonStyle : {}),
            }}
            onClick={() => handleChartClick("inventory")}
          >
            Inventory Analytics
          </button>
          {activeChart === "inventory" && (
            <div style={chartContainer}>
              <InventoryAnalytics />
            </div>
          )}

        <button     
            style={{
              ...chartButton,
              ...(activeChart === "prebuild" ? activeButtonStyle : {}),
            }}
            onClick={() => handleChartClick("prebuild")}
          >
            Pre-Builds Analytics
          </button>
          {activeChart === "prebuild" && (
            <div style={chartContainer}>
              <PreBuildAnalytics />
            </div>
          )}

          <button
            style={{
              ...chartButton,
              ...(activeChart === "inquiry" ? activeButtonStyle : {}),
            }}
            onClick={() => handleChartClick("inquiry")}
          >
            Inquiry Analytics
          </button>
          {activeChart === "inquiry" && (
            <div style={chartContainer}>
              <InquiryChart />
            </div>
          )}

          <button
            style={{
              ...chartButton,
              ...(activeChart === "review" ? activeButtonStyle : {}),
            }}
            onClick={() => handleChartClick("review")}
          >
            Review Statistics
          </button>
          {activeChart === "review" && (
            <div style={chartContainer}>
              <ReviewChart />
            </div>
          )}

          <button
            style={{
              ...chartButton,
              ...(activeChart === "appointment" ? activeButtonStyle : {}),
            }}
            onClick={() => handleChartClick("appointment")}
          >
            Appointment Overview
          </button>
          {activeChart === "appointment" && (
            <div style={chartContainer}>
              <AppointmentAnalytics />
            </div>
          )}

          <button
            style={{
              ...chartButton,
              ...(activeChart === "order" ? activeButtonStyle : {}),
            }}
            onClick={() => handleChartClick("order")}
          >
            Order Overview
          </button>
          {activeChart === "order" && (
            <div style={chartContainer}>
              <OrderChart />
            </div>
          )}

          <button
            style={{
              ...chartButton,
              ...(activeChart === "Successorder" ? activeButtonStyle : {}),
            }}
            onClick={() => handleChartClick("Successorder")}
          >
            SuccessOrder Overview
          </button>
          {activeChart === "Successorder" && (
            <div style={chartContainer}>
              <OrderSuccessDashboard />
            </div>
          )}

          <button
            style={{
              ...chartButton,
              ...(activeChart === "transaction" ? activeButtonStyle : {}),
            }}
            onClick={() => handleChartClick("transaction")}
          >
            Transaction Analytics
          </button>
          {activeChart === "transaction" && (
            <div style={chartContainer}>
              <TransactionDashboard />
            </div>
          )}
        </section>
      </main>
    </div>
  );
};

// --- Lighter Purple and White Gradient Theme - Improved ---
const dashboardBackgroundGradient = "linear-gradient(135deg, #e0d8f1, #ffffff)";
const sectionBackgroundGradient = "linear-gradient(135deg, #f0e5f7, #ffffff)";
const accentColor = "#9b5bdb";
const activeColor = "#7c3aed"; // A slightly darker, solid purple for active state

const dashboardContainer = {
  padding: "15px", // Reduced padding
  display: "flex",
  flexDirection: "column",
  minHeight: "100vh",
  gap: "10px", // Reduced gap
  background: dashboardBackgroundGradient,
  color: "#333",
  fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
};

const mainContent = {
  flexGrow: 1,
  display: "flex",
  flexDirection: "column",
  gap: "8px", // Reduced gap
};

const chartListSection = {
  background: sectionBackgroundGradient,
  padding: "25px", // Slightly reduced padding
  borderRadius: "12px",
  boxShadow: "0 0 8px rgba(155, 91, 219, 0.2)",
  border: `1px solid ${accentColor}`,
  display: "flex",
  flexDirection: "column",
  alignItems: "stretch", // Stretch buttons to full width
};

const chartButton = {
  width: "100%", // Full width buttons
  padding: "12px 20px", // Slightly reduced vertical padding
  marginBottom: "15px", // Reduced margin
  fontSize: "1.2rem", // Slightly smaller font size
  fontWeight: "bold",
  color: accentColor,
  background: "transparent",
  border: `2px solid ${accentColor}`,
  borderRadius: "8px", // Slightly less rounded
  cursor: "pointer",
  transition: "background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease",
  textTransform: "uppercase",
  letterSpacing: "1px", // Reduced letter spacing
  boxShadow: "0 0 4px rgba(155, 91, 219, 0.3)",
};

const activeButtonStyle = {
  background: activeColor,
  color: "#fff", // White text on active button
  borderColor: activeColor,
  boxShadow: "0 0 8px rgba(124, 58, 237, 0.5)", // More prominent shadow for active
};

const chartContainer = {
  padding: "15px",
  border: `1px solid ${accentColor}`, // Consistent border color
  borderRadius: "8px",
  marginBottom: "20px", // Increased margin below active chart
  background: "#fff", // Solid white background for better chart contrast
  boxShadow: "0 0 6px rgba(155, 91, 219, 0.2)",
};

export default Dashboard;
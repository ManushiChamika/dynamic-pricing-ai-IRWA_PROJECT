import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";

const SuccessOrder = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showCustomer, setShowCustomer] = useState(false);
  const [newStatus, setNewStatus] = useState("");

  useEffect(() => {
    const fetchOrder = async () => {
      try {
        const token = localStorage.getItem("token");
        if (!token) {
          navigate("/login");
          return;
        }

        const response = await fetch(`http://localhost:5000/api/successorders/admin/${id}`, {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) throw new Error("Failed to fetch success order");

        const data = await response.json();
        setOrder(data);
      } catch (error) {
        console.error("Error fetching success order:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchOrder();
  }, [id, navigate]);

  const handleStatusUpdate = async () => {
    if (!newStatus) {
      alert("Please select a status to update.");
      return;
    }

    if (newStatus === "handedOver" && order.status !== "Approved") {
      alert("Order must be Approved before it can be Handed Over.");
      return;
    }

    // Check if the order is Fraudulent
    if (order.isFraudulent === true) {
      const reason = order.fraudReason || "No specific reason provided."; // Show reason if available
      const confirmManualCheck = window.confirm(
        `This order is marked as Fraudulent.\nReason: ${reason}\nPlease ensure a manual check before updating the status.`
      );
      if (!confirmManualCheck) {
        return; // If admin cancels, stop the update
      }
    }

    // ⏰ Check if 24 hours passed since createdAt
    const createdAt = new Date(order.createdAt);
    const now = new Date();
    const hoursPassed = (now - createdAt) / (1000 * 60 * 60); // milliseconds to hours

    if (hoursPassed < 24) {
      // alert("You can update the status only after 24 hours from order creation!");
      // return;
      const confirmUpdate = window.confirm(
        `It's been only ${hoursPassed.toFixed(2)} hours since order creation.\nAre you sure you want to update the status now?`
      );
      if (!confirmUpdate) {
        return; // If admin cancels, stop the update
      }
    }

    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`http://localhost:5000/api/successorders/admin/updatestatus/${id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ status: newStatus }),
      });

      if (!response.ok) throw new Error("Failed to update status");

      const updatedOrder = await response.json();
      setOrder(updatedOrder);

      alert(`Status updated to ${newStatus}. An email will be sent to the customer.`);
    } catch (error) {
      console.error("Error updating status:", error);
      alert("Failed to update order status.");
    }
  };

  const generateReport = () => {
    const reportWindow = window.open("", "_blank");
    if (!reportWindow) return alert("Popup blocked! Please allow popups for this site.");

    const customer = order.customerId;
    const orderItems = order.items.map(
      (item, index) => `
        <tr>
          <td style="border: 1px solid #333; padding: 8px;">${item.itemType}</td>
          <td style="border: 1px solid #333; padding: 8px;">${item.quantity}</td>
          <td style="border: 1px solid #333; padding: 8px;">${item.specs.map(spec => `${spec.label}: ${spec.value}`).join(", ")}</td>
        </tr>
      `
    ).join("");

    reportWindow.document.write(`
      <html>
      <head>
        <title>Alpha IT Solutions - Order Report</title>
      </head>
      <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h1 style="color: #00bcd4;">Order Report</h1>
        
        <h2>Order Details</h2>
        <p><strong>Total Amount:</strong> LKR ${order.totalAmount.toFixed(2)}</p>
        <p><strong>Status:</strong> ${order.status}</p>
        <p><strong>Created At:</strong> ${new Date(order.createdAt).toLocaleString()}</p>
  
        <h2>Customer Details</h2>
        <p><strong>Name:</strong> ${customer?.name || "N/A"}</p>
        <p><strong>Email:</strong> ${customer?.email || "N/A"}</p>
        <p><strong>Contact Number:</strong> ${customer?.contactNumber || "N/A"}</p>
  
        <h2>Items Ordered</h2>
        <table style="width: 100%; border-collapse: collapse; background-color: #f9f9f9;">
          <thead>
            <tr style="background-color: #e0e0e0;">
              <th style="border: 1px solid #000; padding: 10px;">Item Type</th>
              <th style="border: 1px solid #000; padding: 10px;">Quantity</th>
              <th style="border: 1px solid #000; padding: 10px;">Specifications</th>
            </tr>
          </thead>
          <tbody>
            ${orderItems}
          </tbody>
        </table>
  
        <br>
        <p style="color: gray;">Generated on ${new Date().toLocaleString()}</p>
      </body>
      </html>
    `);

    reportWindow.document.close();
    reportWindow.print();
  };

  if (loading) return <div>Loading order details...</div>;
  if (!order) return <div>Order not found.</div>;

  return (
    <div
      className="success-order-container"
      style={{
        padding: "20px",
        backgroundColor: "#121212",
        minHeight: "100vh",
        color: "#ffffff",
        fontFamily: "Arial, sans-serif",
      }}
    >
      <h1 style={{ marginBottom: "20px", color: "#00bcd4", fontSize: "30px" }}>Order Details</h1>

      {/* Basic Order Details */}
      <div style={{ marginBottom: "30px", backgroundColor: "#1e1e1e", padding: "20px", borderRadius: "8px" }}>
        {/* <div><strong>Order ID:</strong> {order._id}</div>
        <div><strong>Customer ID:</strong> {order.customerId?._id || order.customerId}</div> */}
        <div><strong>Total Amount:</strong> LKR {order.totalAmount.toFixed(2)}</div>
        <div><strong>Status:</strong> {order.status}</div>
        <div><strong>Created At:</strong> {new Date(order.createdAt).toLocaleString()}</div>

        {/* Toggle customer details */}
        <button
          onClick={() => setShowCustomer(!showCustomer)}
          style={{
            marginTop: "15px",
            padding: "10px 20px",
            backgroundColor: "#00bcd4",
            color: "#121212",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
            fontWeight: "bold",
          }}
        >
          {showCustomer ? "Hide Customer Details" : "View Customer Details"}
        </button>

        {showCustomer && order.customerId && typeof order.customerId === "object" && (
          <div style={{ marginTop: "20px", backgroundColor: "#2c2c2c", padding: "15px", borderRadius: "8px" }}>
            <h3 style={{ color: "#00bcd4" }}>Customer Details:</h3>
            <div><strong>Name:</strong> {order.customerId.name}</div>
            <div><strong>Email:</strong> {order.customerId.email}</div>
            <div><strong>Contact Number:</strong> {order.customerId.contactNumber}</div>
          </div>
        )}
      </div>

      {/* Status Update Section */}
      <div style={{ marginBottom: "30px", backgroundColor: "#1e1e1e", padding: "20px", borderRadius: "8px" }}>
        <h2 style={{ color: "#00bcd4" }}>Update Order Status</h2>
        <select
          value={newStatus}
          onChange={(e) => setNewStatus(e.target.value)}
          style={{
            marginTop: "10px",
            padding: "10px",
            borderRadius: "6px",
            border: "1px solid #00bcd4",
            backgroundColor: "#2c2c2c",
            color: "#ffffff",
          }}
        >
          <option value="Pending">Select Status</option>
          <option value="Approved">Approved</option>
          <option value="Cancelled">Cancelled</option>
          {order.status === "Approved" && <option value="handedOver">HandedOver</option>}
        </select>
        <button
          onClick={handleStatusUpdate}
          style={{
            marginLeft: "10px",
            padding: "10px 20px",
            backgroundColor: "#00bcd4",
            color: "#121212",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
            fontWeight: "bold",
          }}
        >
          Update Status
        </button>
        <button
          onClick={generateReport}
          style={{
            marginLeft: "10px",
            padding: "10px 20px",
            backgroundColor: "#4caf50",
            color: "#ffffff",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
            fontWeight: "bold",
          }}
        >
          Download Report
        </button>
      </div>

      {/* Items Table */}
      <h2 style={{ marginBottom: "10px", color: "#00bcd4" }}>Items</h2>
      {order.items.length > 0 ? (
        <table style={{ width: "100%", borderCollapse: "collapse", backgroundColor: "#1e1e1e" }}>
          <thead>
            <tr>
              {/* <th style={{ border: "1px solid #333", padding: "10px", backgroundColor: "#2c2c2c" }}>Item ID</th> */}
              <th style={{ border: "1px solid #333", padding: "10px", backgroundColor: "#2c2c2c" }}>Item Type</th>
              <th style={{ border: "1px solid #333", padding: "10px", backgroundColor: "#2c2c2c" }}>Quantity</th>
              <th style={{ border: "1px solid #333", padding: "10px", backgroundColor: "#2c2c2c" }}>Specifications</th>
            </tr>
          </thead>
          <tbody>
            {order.items.map((item, index) => (
              <tr key={index}>
                {/* <td style={{ border: "1px solid #333", padding: "10px" }}>{item.itemId}</td> */}
                <td style={{ border: "1px solid #333", padding: "10px" }}>{item.itemType}</td>
                <td style={{ border: "1px solid #333", padding: "10px" }}>{item.quantity}</td>
                <td style={{ border: "1px solid #333", padding: "10px" }}>
                  {item.specs.map((spec, idx) => (
                    <div key={idx}>
                      <strong>{spec.label}:</strong> {spec.value}
                    </div>
                  ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div style={{ marginTop: "10px" }}>No items in this order.</div>
      )}
    </div>
  );
};

export default SuccessOrder;

import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
// import "../../styles/order_dashboard.css";

const OrderList = () => {
  const [orders, setOrders] = useState([]);
  const [filteredOrders, setFilteredOrders] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [isButtonDisabled, setIsButtonDisabled] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchOrders = async () => {
      try {
        const token = localStorage.getItem("token");
        if (!token) {
          navigate("/login");
          return;
        }

        const response = await fetch("http://localhost:5000/api/successorders/successOrder/allOrders", {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error("Failed to fetch orders");
        }

        const data = await response.json();
        setOrders(data);
        setFilteredOrders(data);
      } catch (error) {
        console.error("Error fetching orders:", error);
      }
    };

    fetchOrders();
  }, [navigate]);

  useEffect(() => {
    const filtered = orders.filter((order) =>
      order.status.toLowerCase().includes(searchQuery.toLowerCase())
    );
    setFilteredOrders(filtered);
  }, [searchQuery, orders]);

  const handleRowClick = (order) => {
    setSelectedOrder(order);
    setIsModalOpen(true);
    setIsButtonDisabled(order.status !== "Pending");
  };

  const updateOrderStatus = async (status) => {
    try {
      setIsButtonDisabled(true);
      const token = localStorage.getItem("token");

      const response = await fetch(
        `http://localhost:5000/api/successorders/${selectedOrder._id}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ status }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to update order status");
      }

      const updatedOrder = await response.json();

      setOrders((prev) =>
        prev.map((order) =>
          order._id === updatedOrder._id ? updatedOrder : order
        )
      );

      setFilteredOrders((prev) =>
        prev.map((order) =>
          order._id === updatedOrder._id ? updatedOrder : order
        )
      );

      setIsModalOpen(false);
    } catch (error) {
      console.error("Error updating order:", error);
      setIsButtonDisabled(false);
    }
  };

  const handleGenerateFullReport = () => {
    const reportWindow = window.open("", "_blank");

    const tableRows = filteredOrders.map((order, index) => {
      return `
        <tr>
          <td>${index + 1}</td>
          <td>LKR${order.totalAmount.toFixed(2)}</td>
          <td>${order.status}</td>
          <td>${new Date(order.createdAt).toLocaleString()}</td>
        </tr>
      `;
    }).join("");

    const htmlContent = `
      <html>
        <head>
          <title>Alpha IT Solutions</title>
          <title>All Orders Report</title>
          <style>
            body {
              font-family: Arial, sans-serif;
              padding: 20px;
              background-color: #121212;
              color: #eee;
            }
            h2 {
              text-align: center;
              margin-bottom: 20px;
            }
            table {
              width: 100%;
              border-collapse: collapse;
              background-color:rgb(0, 0, 0);
            }
            th, td {
              padding: 10px;
              border: 1px solid #333;
              text-align: left;
            }
            th {
              background-color: #272727;
            }
          </style>
        </head>
        <body>
          <h2>All Orders Report</h2>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Customer ID</th>
                <th>Total Amount</th>
                <th>Status</th>
                <th>Created At</th>
              </tr>
            </thead>
            <tbody>
              ${tableRows}
            </tbody>
          </table>
        </body>
      </html>
    `;

    reportWindow.document.write(htmlContent);
    reportWindow.document.close();
    reportWindow.print();
  };

  return (
    <div style={{ backgroundColor: "#121212", color: "#e0e0e0", minHeight: "100vh", padding: "20px", fontFamily: "'Poppins', sans-serif" }}>
      <div style={{ marginBottom: "20px" }}>
        <h1 style={{ textAlign: "center", color: "#90caf9" }}>Success Order Management</h1>
        <input
          type="text"
          placeholder="Search by status..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            width: "100%",
            padding: "10px",
            borderRadius: "8px",
            border: "1px solid #333",
            backgroundColor: "#1e1e1e",
            color: "#e0e0e0",
            marginTop: "10px",
          }}
        />
      </div>

      <div>
        <button
          onClick={handleGenerateFullReport}
          style={{
            padding: "10px 20px",
            backgroundColor: "#1976d2",
            color: "#fff",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
            marginBottom: "20px",
            display: "block",
            marginLeft: "auto",
            marginRight: "auto",
          }}
        >
          Generate Full Report
        </button>
      </div>

      <div style={{ overflowX: "auto" }}>
        <h2 style={{ marginBottom: "10px" }}>Orders</h2>
        <table style={{ width: "100%", borderCollapse: "collapse", backgroundColor: "#1e1e1e" }}>
          <thead>
            <tr style={{ backgroundColor: "#272727" }}>
              <th style={{ padding: "12px", border: "1px solid #333" }}>ID</th>
              {/* <th style={{ padding: "12px", border: "1px solid #333" }}>Customer ID</th> */}
              <th style={{ padding: "12px", border: "1px solid #333" }}>Total Amount</th>
              <th style={{ padding: "12px", border: "1px solid #333" }}>Status</th>
              <th style={{ padding: "12px", border: "1px solid #333" }}>Created At</th>
            </tr>
          </thead>
          <tbody>
            {filteredOrders.length > 0 ? (
              filteredOrders.map((order, index) => (
                <tr
                  key={order._id}
                  onClick={() => handleRowClick(order)}
                  style={{ cursor: "pointer" }}
                >
                  <td style={{ padding: "10px", border: "1px solid #333" }}>{index + 1}</td>
                  {/* <td style={{ padding: "10px", border: "1px solid #333" }}>{order.customerId}</td> */}
                  <td style={{ padding: "10px", border: "1px solid #333" }}>LKR {order.totalAmount.toFixed(2)}</td>
                  <td style={{ padding: "10px", border: "1px solid #333" }}>{order.status}</td>
                  <td style={{ padding: "10px", border: "1px solid #333" }}>{new Date(order.createdAt).toLocaleString()}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="5" style={{ textAlign: "center", padding: "20px" }}>
                  No orders found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {isModalOpen && selectedOrder && (
        <div style={{
          position: "fixed", top: 0, left: 0, width: "100%", height: "100%",
          backgroundColor: "rgba(0,0,0,0.7)", display: "flex", justifyContent: "center", alignItems: "center",
          zIndex: 1000
        }}>
          <div style={{ backgroundColor: "#1e1e1e", padding: "30px", borderRadius: "10px", width: "90%", maxWidth: "500px", color: "#e0e0e0" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h2>Order Details</h2>
              <button onClick={() => setIsModalOpen(false)} style={{
                background: "transparent",
                border: "none",
                fontSize: "24px",
                color: "#f44336",
                cursor: "pointer"
              }}>&times;</button>
            </div>
            <div style={{ marginTop: "20px" }}>
              {/* <p><strong>Customer ID:</strong> {selectedOrder.customerId}</p> */}
              <p><strong>Total Amount:</strong> LKR {selectedOrder.totalAmount.toFixed(2)}</p>
              <p><strong>Status:</strong> {selectedOrder.status}</p>
              <p><strong>Created At:</strong> {new Date(selectedOrder.createdAt).toLocaleString()}</p>

              <div style={{ marginTop: "20px", display: "flex", gap: "10px" }}>
                <button
                  onClick={() => {
                    if (window.confirm("Are you sure you want to approve this order?")) {
                      updateOrderStatus("Approved");
                    }
                  }}
                  disabled={isButtonDisabled}
                  style={{
                    flex: 1,
                    padding: "10px",
                    backgroundColor: isButtonDisabled ? "#555" : "#4caf50",
                    color: "#fff",
                    border: "none",
                    borderRadius: "6px",
                    cursor: isButtonDisabled ? "not-allowed" : "pointer",
                  }}
                >
                  Approve
                </button>

                <button
                  onClick={() => {
                    if (window.confirm("Are you sure you want to cancel this order?")) {
                      updateOrderStatus("Cancelled");
                    }
                  }}
                  disabled={isButtonDisabled}
                  style={{
                    flex: 1,
                    padding: "10px",
                    backgroundColor: isButtonDisabled ? "#555" : "#f44336",
                    color: "#fff",
                    border: "none",
                    borderRadius: "6px",
                    cursor: isButtonDisabled ? "not-allowed" : "pointer",
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OrderList;

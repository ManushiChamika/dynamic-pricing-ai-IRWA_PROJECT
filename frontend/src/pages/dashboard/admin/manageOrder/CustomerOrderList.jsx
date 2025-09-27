import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

const CustomerOrderList = () => {
  const [orders, setOrders] = useState([]);
  const [filteredOrders, setFilteredOrders] = useState([]);
  const [handedOverOrders, setHandedOverOrders] = useState([]);
  const [filteredHandedOverOrders, setFilteredHandedOverOrders] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterMethod, setFilterMethod] = useState("All"); // All, COD, Pickup
  const [showHandedOver, setShowHandedOver] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchOrders = async () => {
      try {
        const token = localStorage.getItem("token");
        if (!token) {
          navigate("/login");
          return;
        }

        const response = await fetch("http://localhost:5000/api/orders/all", {
          method: "GET",
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!response.ok) throw new Error("Failed to fetch customer orders");

        const data = await response.json();
        const handedOver = data.filter(order => order.SuccessorderId.status === "handedOver");
        const notHandedOver = data.filter(order => order.SuccessorderId.status !== "handedOver");

        setOrders(notHandedOver);
        setHandedOverOrders(handedOver);
        setFilteredOrders(notHandedOver);
        setFilteredHandedOverOrders(handedOver);
      } catch (error) {
        console.error("Error fetching customer orders:", error);
      }
    };

    fetchOrders();
  }, [navigate]);

  useEffect(() => {
    const applyFilters = () => {
      const query = searchQuery.toLowerCase();

      const filterOrderList = (list) => {
        return list.filter(order => {
          const matchesSearch = 
            order.name.toLowerCase().includes(query) || 
            order.paymentMethod.toLowerCase().includes(query);
          
          const matchesMethod =
            filterMethod === "All" ||
            order.paymentMethod === filterMethod;

          return matchesSearch && matchesMethod;
        });
      };

      setFilteredOrders(filterOrderList(orders));
      setFilteredHandedOverOrders(filterOrderList(handedOverOrders));
    };

    applyFilters();
  }, [searchQuery, filterMethod, orders, handedOverOrders]);

  const handleGenerateReport = (ordersToPrint) => {
    const reportWindow = window.open("", "_blank");

    const rows = ordersToPrint.map((order, index) => {
      const cod = order.codDetails || {};
      const pickup = order.pickupDetails || {};
      return ` 
        <tr>
          <td>${index + 1}</td>
          <td>${order.name}</td>
          <td>${order.email}</td>
          <td>${order.phoneNo}</td>
          <td>${order.paymentMethod}</td>
          <td>${order.paymentMethod === "COD" ? cod.address : "-"}</td>
          <td>${order.paymentMethod === "COD" ? new Date(cod.deliveryDate).toLocaleDateString() : new Date(pickup.pickupDate).toLocaleDateString()}</td>
          <td>${order.paymentMethod === "COD" ? cod.deliveryTime : pickup.pickupTime}</td>
          <td>${order.SuccessorderId.status}</td>
          <td>${new Date(order.createdAt).toLocaleString()}</td>
        </tr>
      `;
    }).join("");

    const html = `
      <html>
        <head>
          <title>Customer Orders Report</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 20px; background-color: #121212; color: #fff; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 15px; border: 1px solid #333; }
            th { background-color: #1f1f1f; color: #fff; text-align: left; }
            tr:nth-child(even) { background-color: #2c2c2c; }
            tr:hover { background-color: #3c3c3c; }
          </style>
        </head>
        <body>
          <h2>Customer Orders Report</h2>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Method</th>
                <th>Address</th>
                <th>Date</th>
                <th>Time</th>
                <th>Status</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              ${rows}
            </tbody>
          </table>
        </body>
      </html>
    `;

    reportWindow.document.write(html);
    reportWindow.document.close();
    reportWindow.print();
  };

  const handleOrderClick = (orderId) => {
    navigate(`/dashboard/SuccessOrder/${orderId}`);
  };

  const toggleHandedOverTable = () => {
    setShowHandedOver(!showHandedOver);
  };

  const getOrderBackgroundColor = (order) => {
    const cod = order.codDetails || {};
    const pickup = order.pickupDetails || {};
    const currentDate = new Date();
    let scheduledDate;

    if (order.paymentMethod === "COD") {
      scheduledDate = cod.deliveryDate ? new Date(cod.deliveryDate) : null;
    } else {
      scheduledDate = pickup.pickupDate ? new Date(pickup.pickupDate) : null;
    }

    if (order.SuccessorderId.status === "handedOver" && scheduledDate && scheduledDate > currentDate) {
      return "#374151";
    }

    return "transparent";
  };

  return (
    <div className="dashboard-container" style={{ backgroundColor: "#121212", color: "#fff", minHeight: "100vh", padding: "20px" }}>
      <h1>Customer Orders</h1>

      <div style={{ marginBottom: "15px" }}>
        <input
          type="text"
          placeholder="Search by name or method..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{ padding: "10px", width: "250px", marginRight: "10px", borderRadius: "5px", backgroundColor: "#000", color: "#fff", border: "1px solid #555" }}
        />

        <select
          value={filterMethod}
          onChange={(e) => setFilterMethod(e.target.value)}
          style={{ padding: "10px", marginRight: "10px", borderRadius: "5px", backgroundColor: "#333", color: "#fff", border: "1px solid #555" }}
        >
          <option style={{ color: "white" }} value="All">All Methods</option>
          <option style={{ color: "white" }} value="COD">COD</option>
          <option style={{ color: "white" }} value="Pickup">Pickup</option>
        </select>

        <button
          onClick={() => handleGenerateReport(showHandedOver ? filteredHandedOverOrders : filteredOrders)}
          style={{
            padding: "10px 20px",
            backgroundColor: "#4CAF50",
            color: "#fff",
            border: "none",
            borderRadius: "5px",
            cursor: "pointer"
          }}
        >
          Generate Report
        </button>
      </div>

      <div style={{ overflowX: "auto", overflowY: "auto", maxHeight: "500px", marginBottom: "30px" }}>
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Name</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Payment Method</th>
              <th>Address</th>
              <th>Date</th>
              <th>Time</th>
              <th>Status</th>
              <th>Created At</th>
            </tr>
          </thead>
          <tbody>
            {(showHandedOver ? filteredHandedOverOrders : filteredOrders).length > 0 ? (
              (showHandedOver ? filteredHandedOverOrders : filteredOrders).map((order, index) => {
                const cod = order.codDetails || {};
                const pickup = order.pickupDetails || {};

                return (
                  <tr
                    key={order._id}
                    onClick={() => handleOrderClick(order.SuccessorderId._id)}
                    style={{
                      cursor: "pointer",
                      backgroundColor: getOrderBackgroundColor(order),
                    }}
                  >
                    <td style={{ border: "1px solid #333", padding: "10px" }}>{index + 1}</td>
                    <td style={{ border: "1px solid #333", padding: "10px" }}>{order.name}</td>
                    <td style={{ border: "1px solid #333", padding: "10px" }}>{order.email}</td>
                    <td style={{ border: "1px solid #333", padding: "10px" }}>{order.phoneNo}</td>
                    <td style={{ border: "1px solid #333", padding: "10px" }}>{order.paymentMethod}</td>
                    <td style={{ border: "1px solid #333", padding: "10px" }}>{order.paymentMethod === "COD" ? cod.address : "-"}</td>
                    <td style={{ border: "1px solid #333", padding: "10px" }}>
                      {order.paymentMethod === "COD"
                        ? cod.deliveryDate
                          ? new Date(cod.deliveryDate).toLocaleDateString()
                          : "-"
                        : pickup.pickupDate
                        ? new Date(pickup.pickupDate).toLocaleDateString()
                        : "-"}
                    </td>
                    <td style={{ border: "1px solid #333", padding: "10px" }}>
                      {order.paymentMethod === "COD"
                        ? cod.deliveryTime || "-"
                        : pickup.pickupTime || "-"}
                    </td>
                    <td style={{ border: "1px solid #333", padding: "10px" }}>{order.SuccessorderId.status}</td>
                    <td style={{ border: "1px solid #333", padding: "10px" }}>{new Date(order.createdAt).toLocaleString()}</td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan="10" style={{ textAlign: "center" }}>
                  No orders found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <button
        onClick={toggleHandedOverTable}
        style={{
          padding: "10px 20px",
          marginTop: "20px",
          backgroundColor: "#FF5722",
          color: "#fff",
          border: "none",
          borderRadius: "5px",
          cursor: "pointer"
        }}
      >
        {showHandedOver ? "Show Pending Orders" : "Show Handed Over Orders"}
      </button>
    </div>
  );
};

export default CustomerOrderList;

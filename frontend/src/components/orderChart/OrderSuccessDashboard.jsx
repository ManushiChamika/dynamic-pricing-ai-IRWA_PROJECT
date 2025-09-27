import React, { useEffect, useState } from "react";
import axios from "axios";
import { Bar, Pie } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement } from 'chart.js';

// ChartJS registration
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

function OrderSuccessDashboard() {
  const [orders, setOrders] = useState([]);
  const [successOrders, setSuccessOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: "", text: "" });

  useEffect(() => {
    fetchOrders();
    const interval = setInterval(fetchOrders, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchOrders = async () => {
    try {
      const token = localStorage.getItem("token");
      const orderRes = await axios.get("http://localhost:5000/api/orders/all", {
        headers: { Authorization: `Bearer ${token}` }
      });
      const successOrderRes = await axios.get("http://localhost:5000/api/successorders/successOrder/allOrders", {
        headers: { Authorization: `Bearer ${token}` }
      });

      setOrders(orderRes.data || []);
      setSuccessOrders(successOrderRes.data || []);
    } catch (error) {
      console.error(error);
      setMessage({ type: "error", text: "Failed to fetch orders." });
    }
  };

  const getAnalyticsData = () => {
    const totalOrders = orders.length;
    const fraudOrders = orders.filter(order => order.isFraudulent).length;
    const paymentMethods = {
      COD: orders.filter(order => order.paymentMethod === "COD").length,
      Pickup: orders.filter(order => order.paymentMethod === "Pickup").length
    };

    const totalSuccessOrders = successOrders.length;
    const statusCounts = {
      Pending: successOrders.filter(o => o.status === "Pending").length,
      Approved: successOrders.filter(o => o.status === "Approved").length,
      Cancelled: successOrders.filter(o => o.status === "Cancelled").length,
      HandedOver: successOrders.filter(o => o.status === "handedOver").length,
    };

    // Count item types (Product vs PreBuild)
    let productCount = 0;
    let prebuildCount = 0;
    successOrders.forEach(order => {
      order.items.forEach(item => {
        if (item.itemType === "Product") productCount += item.quantity;
        else if (item.itemType === "PreBuild") prebuildCount += item.quantity;
      });
    });

    // Last 7 days trend
    const last7Days = [...Array(7)].map((_, i) => {
      const d = new Date();
      d.setDate(d.getDate() - i);
      return d.toISOString().split('T')[0];
    }).reverse();

    const dailyOrderCounts = last7Days.map(date => 
      orders.filter(order => new Date(order.createdAt).toISOString().split('T')[0] === date).length
    );

    const dailySuccessOrderCounts = last7Days.map(date => 
      successOrders.filter(order => new Date(order.createdAt).toISOString().split('T')[0] === date).length
    );

    // KPI Calculations
    const totalRevenue = successOrders.reduce((sum, order) => sum + order.totalAmount, 0);
    const averageOrderValue = totalRevenue / totalSuccessOrders || 0;

    const uniqueCustomers = new Set(orders.map(order => order.customerId));
    const averageOrderFrequency = totalOrders / uniqueCustomers.size || 0;

    return {
      totalOrders,
      fraudOrders,
      paymentMethods,
      totalSuccessOrders,
      statusCounts,
      productCount,
      prebuildCount,
      last7Days,
      dailyOrderCounts,
      dailySuccessOrderCounts,
      averageOrderValue,
      averageOrderFrequency,
      uniqueCustomersSize: uniqueCustomers.size,
    };
  };

  const analytics = getAnalyticsData();

  const paymentMethodChartData = {
    labels: ["COD", "Pickup"],
    datasets: [{
      label: "Payment Methods",
      data: [analytics.paymentMethods.COD, analytics.paymentMethods.Pickup],
      backgroundColor: ["#36A2EB", "#FF6384"],
    }],
  };

  const fraudChartData = {
    labels: ["Fraudulent", "Genuine"],
    datasets: [{
      label: "Fraud Analysis",
      data: [analytics.fraudOrders, analytics.totalOrders - analytics.fraudOrders],
      backgroundColor: ["#FF6384", "#4BC0C0"],
    }],
  };

  const successStatusChartData = {
    labels: Object.keys(analytics.statusCounts),
    datasets: [{
      label: "Success Order Status",
      data: Object.values(analytics.statusCounts),
      backgroundColor: ["#FFCE56", "#36A2EB", "#FF6384", "#9966FF"],
    }],
  };

  const itemTypeChartData = {
    labels: ["Product", "PreBuild"],
    datasets: [{
      label: "Items Sold",
      data: [analytics.productCount, analytics.prebuildCount],
      backgroundColor: ["#4BC0C0", "#FF9F40"],
    }],
  };

  const orderTrendChartData = {
    labels: analytics.last7Days.map(date => new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })),
    datasets: [
      {
        label: "Orders",
        data: analytics.dailyOrderCounts,
        backgroundColor: "#36A2EB",
      },
      {
        label: "Success Orders",
        data: analytics.dailySuccessOrderCounts,
        backgroundColor: "#4BC0C0",
      },
    ],
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <MessageDisplay message={message} />
      
      <h3 className="text-4xl font-bold text-center mb-10 text-gray-800">
        📦 Order & Success Order Dashboard
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
        <InfoCard title="Total Orders" value={analytics.totalOrders} color="bg-blue-500" icon="📦" />
        <InfoCard title="Fraudulent Orders" value={analytics.fraudOrders} color="bg-orange-400" icon="🚨" />
        <InfoCard title="Total Success Orders" value={analytics.totalSuccessOrders} color="bg-green-400" icon="✅" />
        <InfoCard title="Products Sold" value={analytics.productCount + analytics.prebuildCount} color="bg-yellow-500" icon="🛍️" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
        <InfoCard title="Avg Order Value" value={`LKR ${analytics.averageOrderValue.toFixed(2)}`} color="bg-purple-500" icon="💲" />
        <InfoCard title="Avg Order Frequency" value={analytics.averageOrderFrequency.toFixed(2)} color="bg-teal-500" icon="🔄" />
        <InfoCard title="Unique Customers" value={analytics.uniqueCustomersSize} color="bg-indigo-500" icon="👥" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <ChartCard title="Payment Methods" chart={<Pie data={paymentMethodChartData} />} />
        <ChartCard title="Fraudulent Analysis" chart={<Pie data={fraudChartData} />} />
        <ChartCard title="Success Order Status" chart={<Pie data={successStatusChartData} />} />
        <ChartCard title="Items Sold (Product vs PreBuild)" chart={<Pie data={itemTypeChartData} />} />
        <ChartCard title="Order Trends (7 days)" chart={<Bar data={orderTrendChartData} />} />
      </div>
    </div>
  );
}

// Helper Components
const InfoCard = ({ title, value, color, icon }) => (
  <div className={`p-6 rounded-lg shadow-lg ${color} text-white text-center`}>
    <div className="flex items-center justify-center mb-4 text-3xl">{icon}</div>
    <h4 className="text-sm">{title}</h4>
    <p className="text-2xl font-bold">{value}</p>
  </div>
);

const ChartCard = ({ title, chart }) => (
  <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
    <h4 className="font-semibold text-gray-700 mb-4">{title}</h4>
    <div className="h-64">{chart}</div>
  </div>
);

// Message Component
const MessageDisplay = ({ message }) => {
  if (!message.text) return null;
  return (
    <div className={`p-4 my-4 text-white rounded-md ${message.type === "success" ? "bg-green-500" : "bg-red-500"}`}>
      {message.text}
    </div>
  );
};

export default OrderSuccessDashboard;

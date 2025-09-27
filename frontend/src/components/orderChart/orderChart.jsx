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

function OrderChart() {
    const [orders, setOrders] = useState([]);
    const [message, setMessage] = useState({ type: "", text: "" });

    useEffect(() => {
        fetchOrders();
        const interval = setInterval(fetchOrders, 30000); // auto refresh every 30s
        return () => clearInterval(interval);
    }, []);

    const fetchOrders = async () => {
        try {
            const token = localStorage.getItem("token");
            const { data } = await axios.get("http://localhost:5000/api/orders/all", {
                headers: { Authorization: `Bearer ${token}` }
            });

            // process dates
            const processed = data.map(order => ({
                ...order,
                createdAt: order.createdAt ? new Date(order.createdAt) : new Date(),
            })).sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));            

            setOrders(processed);
        } catch (error) {
            setMessage({ type: "error", text: "Failed to fetch orders." });
            console.error("Fetch error:", error.response?.data || error.message);
        }
    };

    const getAnalyticsData = () => {
        const validOrders = orders.filter(order => order.createdAt && !isNaN(new Date(order.createdAt).getTime()));
        
        const totalOrders = validOrders.length;

        const paymentCounts = {
            COD: validOrders.filter(o => o.paymentMethod === "COD").length,
            Pickup: validOrders.filter(o => o.paymentMethod === "Pickup").length
        };

        const fraudCounts = {
            Fraudulent: validOrders.filter(o => o.isFraudulent).length,
            Genuine: validOrders.filter(o => !o.isFraudulent).length
        };

        const last7Days = [...Array(7)].map((_, i) => {
            const d = new Date();
            d.setDate(d.getDate() - i);
            return d.toISOString().split('T')[0];
        }).reverse();

        const dailyCounts = last7Days.map(date => 
            validOrders.filter(order => {
                const orderDate = new Date(order.createdAt).toISOString().split('T')[0];
                return orderDate === date;
            }).length
        );

        // Calculate average orders per day (frequency)
        const totalDays = (validOrders.length > 0) ? Math.ceil(
            (new Date() - new Date(validOrders[validOrders.length - 1].createdAt)) / (1000 * 60 * 60 * 24)
        ) : 1; // prevent division by zero
        const avgOrdersPerDay = totalDays ? (totalOrders / totalDays).toFixed(2) : 0;

        return { totalOrders, paymentCounts, fraudCounts, last7Days, dailyCounts, avgOrdersPerDay };
    };

    const analytics = getAnalyticsData();

    const paymentChartData = {
        labels: ["COD", "Pickup"],
        datasets: [
            {
                label: 'Payment Methods',
                data: [analytics.paymentCounts.COD, analytics.paymentCounts.Pickup],
                backgroundColor: ['#4caf50', '#2196f3'],
                borderColor: ['#388e3c', '#1976d2'],
                borderWidth: 1,
            },
        ],
    };

    const fraudChartData = {
        labels: ["Genuine", "Fraudulent"],
        datasets: [
            {
                label: 'Fraud Status',
                data: [analytics.fraudCounts.Genuine, analytics.fraudCounts.Fraudulent],
                backgroundColor: ['#00c853', '#d50000'],
                borderColor: ['#00c853', '#d50000'],
                borderWidth: 1,
            },
        ],
    };

    const trendChartData = {
        labels: analytics.last7Days.map(date => new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })),
        datasets: [
            {
                label: 'Orders per Day',
                data: analytics.dailyCounts,
                backgroundColor: '#7e57c2',
                borderColor: '#5e35b1',
                borderWidth: 1,
            },
        ],
    };

    return (
        <div className="p-8 bg-gray-50 min-h-screen">
            <MessageDisplay message={message} />

            <h3 className="text-4xl font-extrabold mb-6 text-gray-800 uppercase tracking-wide text-center">
                🛒 Order Analytics Dashboard
            </h3>

            {/* Enhanced Stats Section */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 p-6">
                <StatCard title="Total Orders" value={analytics.totalOrders} color="text-green-600" bg="bg-green-50" />
                <StatCard title="Avg Orders/Day" value={analytics.avgOrdersPerDay} color="text-blue-600" bg="bg-blue-50" />
                <StatCard title="Genuine Orders" value={analytics.fraudCounts.Genuine} color="text-indigo-600" bg="bg-indigo-50" />
                <StatCard title="Fraudulent Orders" value={analytics.fraudCounts.Fraudulent} color="text-red-600" bg="bg-red-50" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 p-6">
                <div className="bg-white p-4 rounded-xl">
                    <h4 className="font-medium text-gray-700 mb-3">Payment Method</h4>
                    <div className="h-64">
                        <Pie data={paymentChartData} options={{ responsive: true, maintainAspectRatio: false }} />
                    </div>
                </div>

                <div className="bg-white p-4 rounded-xl">
                    <h4 className="font-medium text-gray-700 mb-3">Fraud Analysis</h4>
                    <div className="h-64">
                        <Pie data={fraudChartData} options={{ responsive: true, maintainAspectRatio: false }} />
                    </div>
                </div>

                <div className="bg-white p-4 rounded-xl">
                    <h4 className="font-medium text-gray-700 mb-3">Order Trend</h4>
                    <div className="h-64">
                        <Bar data={trendChartData} options={{ responsive: true, maintainAspectRatio: false }} />
                    </div>
                </div>
            </div>
        </div>
    );
}

// Message Component
const MessageDisplay = ({ message }) => {
    if (!message.text) return null;

    return (
        <div className={`p-4 my-4 text-white rounded-lg ${message.type === "success" ? "bg-green-500" : "bg-red-500"}`}>
            {message.text}
        </div>
    );
};

// Reusable Stat Card Component
const StatCard = ({ title, value, color, bg }) => (
    <div className={`${bg} p-6 rounded-xl`}>
        <div className={`${color} font-semibold mb-2`}>{title}</div>
        <div className="text-3xl font-bold">{value}</div>
    </div>
);

export default OrderChart;

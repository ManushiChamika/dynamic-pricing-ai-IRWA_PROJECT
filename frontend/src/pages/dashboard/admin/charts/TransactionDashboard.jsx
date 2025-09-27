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

function TransactionDashboard() {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: "", text: "" });

  useEffect(() => {
    fetchTransactions();
    const interval = setInterval(fetchTransactions, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchTransactions = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get("http://localhost:5000/api/transactions/all", {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTransactions(response.data || []);
    } catch (error) {
      console.error(error);
      setMessage({ type: "error", text: "Failed to fetch transactions." });
    }
  };

  const getAnalyticsData = () => {
    const totalTransactions = transactions.length;
    const totalIncome = transactions.filter(t => t.type === "Income").reduce((sum, t) => sum + t.amount, 0);
    const totalExpense = transactions.filter(t => t.type === "Expense").reduce((sum, t) => sum + t.amount, 0);
    const suspiciousTransactions = transactions.filter(t => t.isSuspicious).length;

    // Transaction frequency within time window (e.g., hourly)
    const recentTransactionsCount = transactions.filter(t => {
      const oneHourAgo = Date.now() - 60 * 60 * 1000;
      return new Date(t.date).getTime() > oneHourAgo;
    }).length;

    // Fraudulent analysis (transactions flagged as suspicious)
    const fraudAnalysis = transactions.filter(t => t.isSuspicious);

    // Current balance calculation (Income - Expense)
    const currentBalance = totalIncome - totalExpense;

    // Sale trends: Total income per day (or another time period)
    const saleTrends = calculateSaleTrends();

    return {
      totalTransactions,
      totalIncome,
      totalExpense,
      suspiciousTransactions,
      recentTransactionsCount,
      fraudAnalysis,
      currentBalance,
      saleTrends
    };
  };

  const calculateSaleTrends = () => {
    const salesByDate = {};
    transactions.filter(t => t.type === "Income" && t.category === "sales").forEach(t => {
      const date = new Date(t.date).toLocaleDateString(); // Group by date
      salesByDate[date] = (salesByDate[date] || 0) + t.amount;
    });

    return Object.entries(salesByDate).map(([date, amount]) => ({
      date,
      amount
    }));
  };

  const analytics = getAnalyticsData();

  const incomeExpenseChartData = {
    labels: ["Income", "Expense"],
    datasets: [{
      label: "Income vs Expense",
      data: [analytics.totalIncome, analytics.totalExpense],
      backgroundColor: ["#36A2EB", "#FF6384"],
    }],
  };

  const suspiciousTransactionsChartData = {
    labels: ["Suspicious", "Genuine"],
    datasets: [{
      label: "Suspicious Transactions",
      data: [analytics.suspiciousTransactions, analytics.totalTransactions - analytics.suspiciousTransactions],
      backgroundColor: ["#FF6384", "#4BC0C0"],
    }],
  };

  const transactionTrendChartData = {
    labels: ["Last Hour", "Recent Transactions"],
    datasets: [{
      label: "Transaction Trend",
      data: [analytics.recentTransactionsCount, analytics.totalTransactions - analytics.recentTransactionsCount],
      backgroundColor: "#36A2EB",
    }],
  };

  const salesTrendChartData = {
    labels: analytics.saleTrends.map(item => item.date),
    datasets: [{
      label: "Sales Trend",
      data: analytics.saleTrends.map(item => item.amount),
      backgroundColor: "#FFCE56",
    }],
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <MessageDisplay message={message} />
      
      <h3 className="text-4xl font-bold text-center mb-10 text-gray-800">
        💸 Transaction Dashboard
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
        <div className="lg:col-span-4">
          <InfoCard title="Current Balance" value={`LKR ${analytics.currentBalance.toFixed(2)}`} color="bg-purple-500" icon="💰" />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
        <InfoCard title="Total Transactions" value={analytics.totalTransactions} color="bg-blue-500" icon="📊" />
        <InfoCard title="Suspicious Transactions" value={analytics.suspiciousTransactions} color="bg-orange-400" icon="🚨" />
        <InfoCard title="Total Income" value={`LKR ${analytics.totalIncome.toFixed(2)}`} color="bg-green-400" icon="💵" />
        <InfoCard title="Total Expense" value={`LKR ${analytics.totalExpense.toFixed(2)}`} color="bg-red-300" icon="💳" />
        <InfoCard title="Fraudulent Transactions" value={analytics.fraudAnalysis.length} color="bg-yellow-500" icon="🚨" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <ChartCard title="Income vs Expense" chart={<Pie data={incomeExpenseChartData} />} />
        <ChartCard title="Suspicious Transactions" chart={<Pie data={suspiciousTransactionsChartData} />} />
        <ChartCard title="Transaction Trend" chart={<Bar data={transactionTrendChartData} />} />
        <ChartCard title="Sales Trend" chart={<Bar data={salesTrendChartData} />} />
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

export default TransactionDashboard;

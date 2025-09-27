import React, { useEffect, useState } from "react";
import axios from "axios";
import { Bar } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

function AppointmentAnalytics() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: "", text: "" });

  useEffect(() => {
    fetchAppointments();
    // Set up auto-refresh every 30 seconds
    const interval = setInterval(fetchAppointments, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchAppointments = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem("token");
      const { data } = await axios.get("http://localhost:5000/api/appointments/all", {
        headers: { Authorization: `Bearer ${token}` }
      });

      setAppointments(data);
    } catch (error) {
      setMessage({ type: "error", text: "Failed to fetch appointments." });
      console.error("Fetch error:", error.response?.data || error.message);
    } finally {
      setLoading(false);
    }
  };

  const getAnalyticsData = () => {
    const statusCounts = {
      pending: 0,
      accepted: 0,
      rejected: 0
    };

    appointments.forEach((appointment) => {
      if (statusCounts.hasOwnProperty(appointment.status)) {
        statusCounts[appointment.status] = (statusCounts[appointment.status] || 0) + 1;
      }
    });

    // Device type distribution
    const deviceTypeCounts = appointments.reduce((acc, appointment) => {
      const deviceType = appointment.deviceType || "Unknown";
      acc[deviceType] = (acc[deviceType] || 0) + 1;
      return acc;
    }, {});

    // Get top 3 device types
    const topDeviceTypes = Object.entries(deviceTypeCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .reduce((obj, [key, val]) => {
        obj[key] = val;
        return obj;
      }, {});

    // Last 7 days trend
    const last7Days = [...Array(7)].map((_, i) => {
      const d = new Date();
      d.setDate(d.getDate() - i);
      return d.toISOString().split('T')[0];
    }).reverse();

    const dailyCounts = last7Days.map(date => {
      return appointments.filter(appointment => {
        const appointmentDate = appointment.date 
          ? new Date(appointment.date).toISOString().split('T')[0] 
          : null;
        return appointmentDate === date;
      }).length;
    });

    return {
      totalAppointments: appointments.length,
      pendingCount: statusCounts.pending,
      acceptedCount: statusCounts.accepted,
      rejectedCount: statusCounts.rejected,
      deviceTypeCounts: topDeviceTypes,
      last7Days,
      dailyCounts
    };
  };

  const analytics = getAnalyticsData();

  const statusChartData = {
    labels: ["Pending", "Accepted", "Rejected"],
    datasets: [
      {
        label: "Appointments by Status",
        data: [
          analytics.pendingCount,
          analytics.acceptedCount,
          analytics.rejectedCount
        ],
        backgroundColor: [
          'rgba(255, 206, 86, 0.7)',
          'rgba(75, 192, 192, 0.7)',
          'rgba(255, 99, 132, 0.7)'
        ],
        borderColor: [
          'rgba(255, 206, 86, 1)',
          'rgba(75, 192, 192, 1)',
          'rgba(255, 99, 132, 1)'
        ],
        borderWidth: 1,
        borderRadius: 4,
      },
    ],
  };

  const deviceChartData = {
    labels: Object.keys(analytics.deviceTypeCounts),
    datasets: [
      {
        label: "Appointments by Device Type",
        data: Object.values(analytics.deviceTypeCounts),
        backgroundColor: 'rgba(54, 162, 235, 0.7)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 1,
        borderRadius: 4,
      },
    ],
  };

  const trendChartData = {
    labels: analytics.last7Days.map(date => 
      new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })),
    datasets: [
      {
        label: "Appointments per Day",
        data: analytics.dailyCounts,
        backgroundColor: 'rgba(255, 159, 64, 0.7)',
        borderColor: 'rgba(255, 159, 64, 1)',
        borderWidth: 1,
        borderRadius: 4,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "top",
        labels: {
          font: {
            size: 14,
          },
          usePointStyle: true,
          padding: 20,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        padding: 12,
        cornerRadius: 8,
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
          drawBorder: false,
        },
        ticks: {
          stepSize: 1
        }
      },
      x: {
        grid: {
          display: false,
          drawBorder: false,
        }
      }
    }
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <MessageDisplay message={message} />
      
      <h3 className="text-4xl font-extrabold mb-6 text-gray-800 uppercase tracking-wide text-center relative">
        <span className="bg-gradient-to-r from-blue-500 to-purple-500 text-transparent bg-clip-text">
          📊 Appointment Analytics Dashboard
        </span>
      </h3>
      
      {/* Analytics Dashboard */}
      <div className="mb-12 bg-white rounded-2xl shadow-lg overflow-hidden border border-gray-200">
        <div className="p-6 bg-gradient-to-r from-blue-600 to-indigo-700 text-white">
          <div className="flex justify-between items-center">
            <h3 className="text-2xl font-bold">📊 Appointment Analytics Dashboard</h3>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 p-6">
          <div className="bg-blue-50 p-6 rounded-xl border border-blue-100">
            <div className="text-blue-600 font-semibold mb-2">Total Appointments</div>
            <div className="text-3xl font-bold text-blue-800">{analytics.totalAppointments}</div>
            <div className="text-sm text-blue-500 mt-2">All time</div>
          </div>
          
          <div className="bg-green-50 p-6 rounded-xl border border-green-100">
            <div className="text-green-600 font-semibold mb-2">Accepted</div>
            <div className="text-3xl font-bold text-green-800">{analytics.acceptedCount}</div>
            <div className="text-sm text-green-500 mt-2">{Math.round((analytics.acceptedCount / analytics.totalAppointments) * 100) || 0}% accepted</div>
          </div>
          
          <div className="bg-yellow-50 p-6 rounded-xl border border-yellow-100">
            <div className="text-yellow-600 font-semibold mb-2">Pending</div>
            <div className="text-3xl font-bold text-yellow-800">{analytics.pendingCount}</div>
            <div className="text-sm text-yellow-500 mt-2">Needs attention</div>
          </div>
          
          <div className="bg-red-50 p-6 rounded-xl border border-red-100">
            <div className="text-red-600 font-semibold mb-2">Rejected</div>
            <div className="text-3xl font-bold text-red-800">{analytics.rejectedCount}</div>
            <div className="text-sm text-red-500 mt-2">{Math.round((analytics.rejectedCount / analytics.totalAppointments) * 100) || 0}% rejected</div>
          </div>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 p-6 border-t border-gray-200">
          <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
            <h4 className="font-medium text-gray-700 mb-3">
              <div className="flex items-center space-x-2">
                <span>By Status</span>
                <span className="flex items-center text-xs space-x-1">
                  <span className="inline-flex items-center">
                    <span className="w-2 h-2 rounded-full bg-yellow-400 mr-1"></span>
                    <span>Pending</span>
                  </span>
                  <span className="inline-flex items-center">
                    <span className="w-2 h-2 rounded-full bg-green-400 mr-1"></span>
                    <span>Accepted</span>
                  </span>
                  <span className="inline-flex items-center">
                    <span className="w-2 h-2 rounded-full bg-red-400 mr-1"></span>
                    <span>Rejected</span>
                  </span>
                </span>
              </div>
            </h4>
            <div className="h-64">
              <Bar data={statusChartData} options={chartOptions} />
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
            <h4 className="font-medium text-gray-700 mb-3">By Device Type</h4>
            <div className="h-64">
              <Bar data={deviceChartData} options={chartOptions} />
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
            <h4 className="font-medium text-gray-700 mb-3">Recent Trend</h4>
            <div className="h-64">
              <Bar data={trendChartData} options={chartOptions} />
            </div>
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

export default AppointmentAnalytics;
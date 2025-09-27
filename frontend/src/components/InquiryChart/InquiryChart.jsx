import React, { useEffect, useState } from "react";
import axios from "axios";
import { Bar, Pie } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement } from 'chart.js';

// Register ChartJS components
ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    ArcElement
  );

function InquiryChart() {
    const [inquiries, setInquiries] = useState([]);
    const [categorizedInquiries, setCategorizedInquiries] = useState({
        General: [],
        ProductAvailability: [],
        Support: [],
    });
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState({ type: "", text: "" });
    const [timeRange, setTimeRange] = useState("all");

    useEffect(() => {
        fetchInquiries();
        // Set up auto-refresh every 30 seconds
        const interval = setInterval(fetchInquiries, 30000);
        return () => clearInterval(interval);
    }, []);

    const fetchInquiries = async () => {
        try {
            const token = localStorage.getItem("token");
            const { data } = await axios.get("http://localhost:5000/api/inquiries/all-inquiries", {
                headers: { Authorization: `Bearer ${token}` }
            });

            // Ensure dates are properly parsed
            const processedInquiries = data.inquiries.map(inquiry => ({
                ...inquiry,
                createdAt: inquiry.createdAt ? new Date(inquiry.createdAt) : new Date(),
                resolvedAt: inquiry.resolvedAt ? new Date(inquiry.resolvedAt) : null
            })).sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));

            setInquiries(processedInquiries);
            setCategorizedInquiries(data.categorizedInquiries);
        } catch (error) {
            setMessage({ type: "error", text: "Failed to fetch inquiries." });
            console.error("Fetch error:", error.response?.data || error.message);
        }
    };

    const getAnalyticsData = () => {
        // Filter out inquiries with invalid dates
        const validInquiries = inquiries.filter(inquiry => 
            inquiry.createdAt && !isNaN(new Date(inquiry.createdAt).getTime())
        );

        const totalInquiries = validInquiries.length;
        const resolvedCount = validInquiries.filter(i => i.status === "Resolved").length;
        const pendingCount = totalInquiries - resolvedCount;
        
        const categoryCounts = {
            General: categorizedInquiries.General.length,
            ProductAvailability: categorizedInquiries.ProductAvailability.length,
            Support: categorizedInquiries.Support.length
        };
        
        const statusCounts = {
            Resolved: resolvedCount,
            Pending: pendingCount
        };
        
        // Generate last 7 days array
        const last7Days = [...Array(7)].map((_, i) => {
            const d = new Date();
            d.setDate(d.getDate() - i);
            return d.toISOString().split('T')[0];
        }).reverse();
        
        // Count inquiries per day
        const dailyCounts = last7Days.map(date => {
            return validInquiries.filter(inquiry => {
                const inquiryDate = new Date(inquiry.createdAt).toISOString().split('T')[0];
                return inquiryDate === date;
            }).length;
        });
        
        return {
            totalInquiries,
            resolvedCount,
            pendingCount,
            categoryCounts,
            statusCounts,
            last7Days,
            dailyCounts
        };
    };
    
    const analytics = getAnalyticsData();

    const categoryChartData = {
        labels: Object.keys(analytics.categoryCounts),
        datasets: [
            {
                label: 'Inquiries by Category',
                data: Object.values(analytics.categoryCounts),
                backgroundColor: [
                    'rgba(54, 162, 235, 0.7)',
                    'rgba(255, 99, 132, 0.7)',
                    'rgba(75, 192, 192, 0.7)'
                ],
                borderColor: [
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 99, 132, 1)',
                    'rgba(75, 192, 192, 1)'
                ],
                borderWidth: 1,
            },
        ],
    };

    const statusChartData = {
        labels: Object.keys(analytics.statusCounts),
        datasets: [
            {
                label: 'Inquiries by Status',
                data: Object.values(analytics.statusCounts),
                backgroundColor: [
                    'rgba(75, 192, 192, 0.7)',
                    'rgba(255, 206, 86, 0.7)'
                ],
                borderColor: [
                    'rgba(75, 192, 192, 1)',
                    'rgba(255, 206, 86, 1)'
                ],
                borderWidth: 1,
            },
        ],
    };

    const trendChartData = {
        labels: analytics.last7Days.map(date => new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })),
        datasets: [
            {
                label: 'Inquiries per Day',
                data: analytics.dailyCounts,
                backgroundColor: 'rgba(153, 102, 255, 0.7)',
                borderColor: 'rgba(153, 102, 255, 1)',
                borderWidth: 1,
            },
        ],
    };

 return (
    <div className="p-8 bg-gray-50 min-h-screen">
        <MessageDisplay message={message} />
        
        <h3 className="text-4xl font-extrabold mb-6 text-gray-800 uppercase tracking-wide text-center relative">
            <span className="bg-gradient-to-r from-blue-500 to-purple-500 text-transparent bg-clip-text">
                📊 Inquiry Analytics Dashboard
            </span>
        </h3>
        
        {/* Analytics Dashboard */}
        <div className="mb-12 bg-white rounded-2xl shadow-lg overflow-hidden border border-gray-200">
            <div className="p-6 bg-gradient-to-r from-blue-600 to-indigo-700 text-white">
                <div className="flex justify-between items-center">
                    <h3 className="text-2xl font-bold">📊 Inquiry Analytics Dashboard</h3>
                    <div className="flex space-x-4">
                        <select 
                            value={timeRange}
                            onChange={(e) => setTimeRange(e.target.value)}
                            className="bg-white bg-opacity-20 border border-white border-opacity-30 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-50"
                        >
                            <option value="all">All Time</option>
                            <option value="week">Last 7 Days</option>
                            <option value="month">Last 30 Days</option>
                        </select>
                    </div>
                </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 p-6">
                <div className="bg-blue-50 p-6 rounded-xl border border-blue-100">
                    <div className="text-blue-600 font-semibold mb-2">Total Inquiries</div>
                    <div className="text-3xl font-bold text-blue-800">{analytics.totalInquiries}</div>
                    <div className="text-sm text-blue-500 mt-2">All time</div>
                </div>
                
                <div className="bg-green-50 p-6 rounded-xl border border-green-100">
                    <div className="text-green-600 font-semibold mb-2">Resolved</div>
                    <div className="text-3xl font-bold text-green-800">{analytics.resolvedCount}</div>
                    <div className="text-sm text-green-500 mt-2">{Math.round((analytics.resolvedCount / analytics.totalInquiries) * 100) || 0}% resolved</div>
                </div>
                
                <div className="bg-yellow-50 p-6 rounded-xl border border-yellow-100">
                    <div className="text-yellow-600 font-semibold mb-2">Pending</div>
                    <div className="text-3xl font-bold text-yellow-800">{analytics.pendingCount}</div>
                    <div className="text-sm text-yellow-500 mt-2">Needs attention</div>
                </div>
                
                <div className="bg-purple-50 p-6 rounded-xl border border-purple-100">
                    <div className="text-purple-600 font-semibold mb-2">Avg. Resolution</div>
                    <div className="text-3xl font-bold text-purple-800">-</div>
                    <div className="text-sm text-purple-500 mt-2">Coming soon</div>
                </div>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 p-6 border-t border-gray-200">
                <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                    <h4 className="font-medium text-gray-700 mb-3">By Category</h4>
                    <div className="h-64">
                        <Pie data={categoryChartData} options={{ responsive: true, maintainAspectRatio: false }} />
                    </div>
                </div>
                
                <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                    <h4 className="font-medium text-gray-700 mb-3">By Status</h4>
                    <div className="h-64">
                        <Pie data={statusChartData} options={{ responsive: true, maintainAspectRatio: false }} />
                    </div>
                </div>
                
                <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                    <h4 className="font-medium text-gray-700 mb-3">Recent Trend</h4>
                    <div className="h-64">
                        <Bar data={trendChartData} options={{ responsive: true, maintainAspectRatio: false }} />
                    </div>
                </div>
            </div>
            
        </div>
    </div>
 )
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

export default InquiryChart
import React, { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "react-toastify";
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

function ReviewChart() {
    const [reviews, setReviews] = useState([]);
    const [message, setMessage] = useState("");
    const [timeRange, setTimeRange] = useState("all");

    useEffect(() => {
        fetchReviews();
    }, []);

    const fetchReviews = async () => {
      try {
        const token = localStorage.getItem("token");
        const { data } = await axios.get("http://localhost:5000/api/reviews/all-reviews", {
          headers: { Authorization: `Bearer ${token}` },
          timeout: 10000
        });
    
        // Handle both array and object responses
        const reviews = Array.isArray(data) ? data : data?.reviews || [];
        setReviews(reviews);
        
      } catch (error) {
        console.error("Fetch Error:", {
          status: error.response?.status,
          message: error.message
        });
        
        toast.error(error.response?.data?.message || "Failed to fetch reviews");
        setReviews([]); // Reset to empty array
      }
    };

    // Analytics functions
    const getAnalyticsData = () => {
        const totalReviews = reviews.length;
        const approvedCount = reviews.filter(r => r.status === "approved").length;
        const pendingCount = reviews.filter(r => r.status === "pending").length;
        const flaggedCount = reviews.filter(r => r.status === "flagged").length;
        
        const ratingCounts = {
            1: reviews.filter(r => r.rating === 1).length,
            2: reviews.filter(r => r.rating === 2).length,
            3: reviews.filter(r => r.rating === 3).length,
            4: reviews.filter(r => r.rating === 4).length,
            5: reviews.filter(r => r.rating === 5).length
        };
        
        const statusCounts = {
            Approved: approvedCount,
            Pending: pendingCount,
            Flagged: flaggedCount
        };
        
        const last7Days = [...Array(7)].map((_, i) => {
            const d = new Date();
            d.setDate(d.getDate() - i);
            return d.toISOString().split('T')[0];
        }).reverse();
        
        const dailyCounts = last7Days.map(date => {
            return reviews.filter(review => {
                if (!review.createdAt) return false;
                const reviewDate = new Date(review.createdAt);
                if (isNaN(reviewDate.getTime())) return false;
                return reviewDate.toISOString().split('T')[0] === date;
            }).length;
        });
        
        return {
            totalReviews,
            approvedCount,
            pendingCount,
            flaggedCount,
            ratingCounts,
            statusCounts,
            last7Days,
            dailyCounts
        };
    };
    
    const analytics = getAnalyticsData();

    const statusChartData = {
        labels: Object.keys(analytics.statusCounts),
        datasets: [
            {
                label: 'Reviews by Status',
                data: Object.values(analytics.statusCounts),
                backgroundColor: [
                    'rgba(75, 192, 192, 0.7)',
                    'rgba(255, 206, 86, 0.7)',
                    'rgba(255, 99, 132, 0.7)'
                ],
                borderColor: [
                    'rgba(75, 192, 192, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(255, 99, 132, 1)'
                ],
                borderWidth: 1,
            },
        ],
    };

    const ratingChartData = {
        labels: Object.keys(analytics.ratingCounts),
        datasets: [
            {
                label: 'Reviews by Rating',
                data: Object.values(analytics.ratingCounts),
                backgroundColor: [
                    'rgba(255, 99, 132, 0.7)',
                    'rgba(255, 159, 64, 0.7)',
                    'rgba(255, 206, 86, 0.7)',
                    'rgba(54, 162, 235, 0.7)',
                    'rgba(75, 192, 192, 0.7)'
                ],
                borderColor: [
                    'rgba(255, 99, 132, 1)',
                    'rgba(255, 159, 64, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(75, 192, 192, 1)'
                ],
                borderWidth: 1,
            },
        ],
    };

    const trendChartData = {
        labels: analytics.last7Days.map(date => new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })),
        datasets: [
            {
                label: 'Reviews per Day',
                data: analytics.dailyCounts,
                backgroundColor: 'rgba(153, 102, 255, 0.7)',
                borderColor: 'rgba(153, 102, 255, 1)',
                borderWidth: 1,
            },
        ],
    };

    return (
      <div className="max-w-full mx-auto p-8 bg-white rounded-xl shadow-lg border border-gray-200">
        <h3 className="text-4xl font-extrabold mb-6 text-gray-800 uppercase tracking-wide text-center relative">
          <span className="bg-gradient-to-r from-blue-500 to-purple-500 text-transparent bg-clip-text">
            📊 Review Analytics Dashboard
          </span>
        </h3>
        {message && <p className="text-red-600 font-semibold text-lg">{message}</p>}
      
        {/* Analytics Dashboard */}
        <div className="mb-12 bg-white rounded-2xl shadow-lg overflow-hidden border border-gray-200">
            <div className="p-6 bg-gradient-to-r from-blue-600 to-indigo-700 text-white">
                <div className="flex justify-between items-center">
                    <h3 className="text-2xl font-bold">📊 Review Analytics Dashboard</h3>
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
                    <div className="text-blue-600 font-semibold mb-2">Total Reviews</div>
                    <div className="text-3xl font-bold text-blue-800">{analytics.totalReviews}</div>
                    <div className="text-sm text-blue-500 mt-2">All time</div>
                </div>
                
                <div className="bg-green-50 p-6 rounded-xl border border-green-100">
                    <div className="text-green-600 font-semibold mb-2">Approved</div>
                    <div className="text-3xl font-bold text-green-800">{analytics.approvedCount}</div>
                    <div className="text-sm text-green-500 mt-2">{Math.round((analytics.approvedCount / analytics.totalReviews) * 100) || 0}% approved</div>
                </div>
                
                <div className="bg-yellow-50 p-6 rounded-xl border border-yellow-100">
                    <div className="text-yellow-600 font-semibold mb-2">Pending</div>
                    <div className="text-3xl font-bold text-yellow-800">{analytics.pendingCount}</div>
                    <div className="text-sm text-yellow-500 mt-2">Needs moderation</div>
                </div>
                
                <div className="bg-red-50 p-6 rounded-xl border border-red-100">
                    <div className="text-red-600 font-semibold mb-2">Flagged</div>
                    <div className="text-3xl font-bold text-red-800">{analytics.flaggedCount}</div>
                    <div className="text-sm text-red-500 mt-2">Requires attention</div>
                </div>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 p-6 border-t border-gray-200">
                <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                    <h4 className="font-medium text-gray-700 mb-3">By Status</h4>
                    <div className="h-64">
                        <Pie data={statusChartData} options={{ responsive: true, maintainAspectRatio: false }} />
                    </div>
                </div>
                
                <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                    <h4 className="font-medium text-gray-700 mb-3">By Rating</h4>
                    <div className="h-64">
                        <Pie data={ratingChartData} options={{ responsive: true, maintainAspectRatio: false }} />
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
    );
}

export default ReviewChart;
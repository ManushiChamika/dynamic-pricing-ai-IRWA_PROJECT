import React, { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "react-toastify";

function ReviewManage() {
    const [reviews, setReviews] = useState([]);
    const [message, setMessage] = useState("");
    const flaggedWords = ["bad", "offensive", "inappropriate"];  // List of flagged words

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

    const handleModerate = async (reviewId, action) => {
        try {
            const token = localStorage.getItem("token");
            const {data} = await axios.put(
                `http://localhost:5000/api/reviews/moderate/${reviewId}`,
                { action },
                { headers: { Authorization: `Bearer ${token}` }, timeout: 10000 }
            );
    
            if (action === "deleted" || action === "rejected") {
              setReviews(prevReviews => prevReviews.filter(review => review._id !== reviewId));
              toast.success(data.message || "Review deleted successfully");
            } else {
              setReviews(prev => prev.map(r => 
                r._id === reviewId ? { ...r, ...data.updatedReview } : r
              ));
              toast.success("Review approved");
            }
        } catch (error) {
          console.error("Moderation Failed:", {
            error: error.response?.data || error.message,
            reviewId,
            action
          });
      
          toast.error(error.response?.data?.message || "Moderation failed");
          fetchReviews(); // Fallback refresh
        }
    };    
    
    // Function to generate stars based on rating
    const renderStars = (rating) => {
        return "★".repeat(rating) + "☆".repeat(5 - rating);
    };

    return (
      <div className="max-w-full mx-auto p-8 bg-white rounded-xl shadow-lg border border-gray-200">
        <h3 className="text-4xl font-extrabold mb-6 text-gray-800 uppercase tracking-wide text-center relative">
          <span className="bg-gradient-to-r from-blue-500 to-purple-500 text-transparent bg-clip-text">
            🛠️ Review Management
          </span>
        </h3>
        {message && <p className="text-red-600 font-semibold text-lg">{message}</p>}
      
        {reviews.length === 0 ? (
          <p className="text-gray-500 text-lg text-center">No reviews found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white border border-gray-300 shadow-md rounded-lg">
              <thead>
                <tr className="bg-gray-800 text-white text-left">
                  <th className="p-4 border w-2/12">Full Name</th>
                  <th className="p-4 border w-2/12">Email</th>
                  <th className="p-4 border w-2/12">Review Title</th>
                  <th className="p-4 border w-1/12">Status</th>
                  <th className="p-4 border w-1/12">Rating</th>
                  <th className="p-4 border w-3/12">Comment</th>
                  <th className="p-4 border w-1/12">Verified Buyer</th>
                  <th className="p-4 border w-1/12">Created At</th>
                  <th className="p-4 border w-1/12">Actions</th>
                </tr>
              </thead>
              <tbody>
                {reviews.map((review) => (
                  <tr
                    key={review._id}
                    className={`border-t hover:bg-gray-100 transition ${
                      review.status === "flagged" ? "bg-red-50" : ""
                    }`}
                  >
                    <td className={`p-4 border w-2/12 font-medium ${review.status === "flagged" ? "text-red-600" : ""}`}>{review.fullName}</td>
                    <td className={`p-4 border w-2/12 ${review.status === "flagged" ? "text-red-600" : ""}`}>{review.email}</td>
                    <td className={`p-4 border w-2/12 ${review.status === "flagged" ? "text-red-600 font-semibold" : ""}`}>{review.reviewTitle}</td>
                    <td
                      className={`p-4 border w-1/12 font-semibold ${
                        review.status === "approved" ? "text-green-600" : "text-red-600"
                      }`}
                    >
                      {review.status}
                    </td>
                    <td className={`p-4 border w-1/12 ${review.status === "flagged" ? "text-red-500" : "text-yellow-500"}`}>{renderStars(review.rating)}</td>
                    <td className={`p-4 border w-3/12 ${review.status === "flagged" ? "text-red-600 font-medium" : ""}`}>{review.comment}</td>
                    <td className={`p-4 border w-1/12 font-semibold ${review.status === "flagged" ? "text-red-600" : ""}`}>
                      {review.verifiedBuyer ? "Yes" : "No"}
                    </td>
                    <td className={`p-4 border w-1/12 ${review.status === "flagged" ? "text-red-500" : ""}`}>
                      {new Date(review.createdAt).toLocaleDateString()}
                    </td>
                    <td className="p-4 border w-12/12 flex flex-col items-center gap-4 py-20">
                      {review.status !== "flagged" ? (
                        <>
                          <button
                            className="bg-green-500 text-white px-4 py-2 rounded-lg shadow hover:bg-green-600 transition"
                            onClick={() => handleModerate(review._id, "approved")}
                          >
                            Approve
                          </button>
                          <button
                            className="bg-red-500 text-white px-4 py-2 rounded-lg shadow hover:bg-red-600 transition"
                            onClick={() => handleModerate(review._id, "rejected")}
                          >
                            Reject
                          </button>
                        </>
                      ) : (
                        <button
                          className="bg-red-600 text-white px-4 py-2 rounded-lg shadow hover:bg-red-700 transition"
                          onClick={() => handleModerate(review._id, "deleted")}
                        >
                          Delete
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    );
}

export default ReviewManage;
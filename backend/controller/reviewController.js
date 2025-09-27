import Review from "../models/reviewModel.js";
import mongoose from "mongoose";
import SuccessOrder from "../models/OrderManagement/SuccessOrder.js";

const inappropriateWords = [
  "useless", "garbage", "piece of crap", "scam", "fraud", "ripoff", "junk",
  "terrible", "horrible", "disappointing", "worst", "awful", "shitty", "pathetic",
  "disgusting", "waste", "overpriced", "defective", "broken", "inferior",
];

export const submitReview = async (req, res) => {
  try {
      const { fullName, email, rating, comment, reviewTitle } = req.body;

      if (!req.user || !req.user._id) {
          return res.status(401).json({ message: "Unauthorized: User ID missing" });
      }

      if (!rating || !comment || !reviewTitle || !fullName || !email) {
          return res.status(400).json({ message: "All required fields must be filled." });
      }

      const userId = new mongoose.Types.ObjectId(req.user._id); // Ensure correct ObjectId type

      // Check if the user has a completed order
      const hasPurchased = await SuccessOrder.findOne({ 
        customerId: userId.toString(),  // Convert userId to string before querying
        status: "Approved" 
      }).maxTimeMS(5000);

      if (!hasPurchased) {
        return res.status(400).json({ message: "Only verified buyers can leave reviews." });
      }

      // Check for inappropriate content (ensure the function exists)
      if (typeof containsInappropriateContent === "function" && containsInappropriateContent(comment)) {
          return res.status(400).json({ message: "Your review contains inappropriate content." });
      }

      let status = "pending";
      let flaggedReason = "";

      // Check for inappropriate words
      for (const word of inappropriateWords) {
          if (comment.toLowerCase().includes(word)) {
              status = "flagged";
              flaggedReason = `Contains inappropriate language: ${word}`;
              break;
          }
      }

      // Create and save review
      const newReview = new Review({
          userId,
          rating,
          comment,
          fullName,
          email,
          reviewTitle,
          verifiedBuyer: true,
          status,
          flaggedReason
      });

      await newReview.save({ maxTimeMS: 5000 });
      res.status(201).json({ message: "Review submitted and pending approval.", reviewId: newReview._id  });

  } catch (error) {
    console.error("🔥 Controller Error:", {
      name: error.name,
      message: error.message,
      stack: error.stack
  });

  if (error.name === 'MongoServerError') {
      return res.status(503).json({ message: "Database operation timed out" });
  }
  res.status(500).json({ 
      message: "Server error",
      error: process.env.NODE_ENV === 'development' ? error.message : undefined
  });
  }
};

//Moderate a Flagged Review (Approve/Reject)
export const moderateReview = async (req, res) => {
  try {
    const { action } = req.body;
    const reviewId = req.params.id;

    if (action.toLowerCase() === "rejected" || action.toLowerCase() === "deleted") {
      // If the review is rejected, delete it from the database
      const deletedReview = await Review.findByIdAndDelete(reviewId)
        .maxTimeMS(5000);

      if (!deletedReview) {
        return res.status(404).json({ message: "Review not found." });
      }

      return res.json({ message: "Review rejected and deleted successfully." });
    }

    // If the review is approved, update the status to "approved"
    const updatedReview = await Review.findByIdAndUpdate(
      reviewId,
      { status: "approved", flaggedReason: "" },
      { new: true, maxTimeMS: 5000 }
    ).lean();

    if (!updatedReview) {
      return res.status(404).json({ message: "Review not found." });
    }

    res.json({ message: "Review approved successfully.", updatedReview });

  } catch (error) {
    console.error("Error updating/deleting review:", error);
    res.status(500).json({ message: "Server error", error });
  }
};

export const getUserReviews = async (req, res) => {
  try {
      const reviews = await Review.find({ userId: req.user.id })
          .maxTimeMS(5000)
          .lean()
          .sort({ createdAt: -1 }) 
      res.json(reviews);
  } catch (error) {
      res.status(500).json({ message: "Server error", error });
  }
};

export const updateReview = async (req, res) => {
  try {
      const { rating, comment, reviewTitle } = req.body; // Extract rating and comment
      const review = await Review.findById(req.params.id)
        .maxTimeMS(5000);
      
      if (!review) {
        return res.status(404).json({ message: "Review not found." });
      }
  
      // Check whether the user is logged in and owns the review
      if (review.userId.toString() !== req.user.id) {
        return res.status(403).json({ message: "Unauthorized" });
      }

      // Check if the review is published
      if (review.status === "approved") {
        return res.status(400).json({ message: "Published reviews cannot be updated." });
      }

      // Check if the review is within the 24-hour edit window
      const timeElapsed = (Date.now() - new Date(review.createdAt)) / (1000 * 60 * 60);
      if (timeElapsed > 24) {
        return res.status(400).json({ message: "You can only edit a review within 24 hours." });
      }

      // Update review
      review.rating = rating;
      review.comment = comment;
      review.reviewTitle = reviewTitle;
      await review.save({ maxTimeMS: 5000});

      res.json({ message: "Review updated successfully.", review });
  } catch (error) {
      console.error("Server error:", error);
      res.status(500).json({ message: "Server error", error });
  }
};

export const deleteReview = async (req, res) => {
  try {
      const { id } = req.params;  // Ensure this matches route
      const review = await Review.findById(id)
         .maxTimeMS(5000);

      if (!review) {
          return res.status(404).json({ message: "Review not found." });
      }

      // Check if the review is published
      if (review.status === "approved") {
        return res.status(400).json({ message: "Published reviews cannot be deleted." });
      }

      const timeElapsed = (Date.now() - new Date(review.createdAt)) / (1000 * 60 * 60);

      if (timeElapsed > 24) {
          return res.status(400).json({ message: "You can only delete a review within 24 hours." });
      }

      await review.deleteOne({maxTimeMS: 5000});
      res.json({ message: "Review deleted successfully." });
  } catch (error) {
      res.status(500).json({ message: "Server error", error });
  }
};

export const approvedReviews = async(req, res) => {
  try {
    const approvedReviews = await Review.find({ status: "approved" })
      .maxTimeMS(5000)
      .lean();
    res.json(approvedReviews);
  } catch (error) {
    res.status(500).json({ error: "Failed to fetch approved reviews" });
  }
};

export const getAllReviews = async (req, res) => {
  try {
      const reviews = await Review.find() // Fetch all reviews from the database
        .maxTimeMS(5000)
        .lean();
      if (!reviews.length) {
          return res.status(404).json({ message: "No reviews found." });
      }

      res.json({ message: "Reviews fetched successfully.", reviews });
  } catch (error) {
      res.status(500).json({ message: "Server error", error });
  }
};
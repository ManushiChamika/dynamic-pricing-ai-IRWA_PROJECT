import mongoose from "mongoose";

const reviewSchema = new mongoose.Schema({
    userId: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true },
    rating: { type: Number, required: true, min: 1, max: 5 },
    comment: { type: String, required: true },
    reviewTitle: { type: String },
    fullName: {type: String, required: true},
    email: {type: String, required: true},
    verifiedBuyer: { type: Boolean, default: false },
    status: { type: String, enum: ["pending", "flagged","approved", "rejected"], default: "pending" },
    createdAt: { type: Date, default: Date.now },
    flaggedReason: { type: String, default: "" },
});

const Review = mongoose.model("Review", reviewSchema);
export default Review;
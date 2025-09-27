import mongoose from "mongoose";

const faqSchema = new mongoose.Schema({
    question: {type:String, required: true},
    answer: {type: String, required: true},
    views: {type: Number, default: 0}, //For tracking most popular FAQs
}, { timestamps: true });

const FAQ = mongoose.model("FAQ", faqSchema);

export default FAQ;
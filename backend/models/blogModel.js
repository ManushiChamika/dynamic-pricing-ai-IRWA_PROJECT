import mongoose from "mongoose";

const blogSchema = new mongoose.Schema({
    title: { type: String, required: true, trim: true},
    content: { type: String, required: true, trim: true },
    image: { type: String, required: true },
    published: { type: Boolean, default: false },
}, { timestamps: true }); // automatic createdAt, updatedAt

const BLOG = mongoose.model("BLOG", blogSchema);

export default BLOG;

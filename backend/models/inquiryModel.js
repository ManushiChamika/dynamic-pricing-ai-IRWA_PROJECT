import mongoose from "mongoose";

const inquirySchema = new mongoose.Schema({
    userId: {type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true},
    fullName: {type: String, required: true},
    email: {type: String, required: true},
    contactNumber: {type: String, required: true},
    inquiryType: {type: String, enum: ['General', 'Product Availability', 'Support'], required: true},
    productName: {type: String},
    additionalDetails: {type: String, required: true},
    attachment: {type: String},
    status: {type: String, enum:['Pending', 'Resolved'], default: 'Pending'},
    createdAt: {type: Date, default: Date.now},
    resolvedAt: { type: Date },
    userApproval: { type: Boolean, default: false },
    adminAnswer: {type: String},
    inquirySubject: {type: String},
});

const Inquiry = mongoose.model("Inquiry", inquirySchema);

export default Inquiry;
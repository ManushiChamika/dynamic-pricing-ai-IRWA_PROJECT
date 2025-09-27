import mongoose from "mongoose";

const taxSchema = new mongoose.Schema({
    successOrderId: { type: mongoose.Schema.Types.ObjectId, ref: 'SuccessOrder', default: 'not from order'  },
    totalAmount: { type: Number, required: true },
    taxAmount: { type: Number, required: true },
    taxRate: { type: Number, default: 0.05 },
    createdAt: { type: Date, default: Date.now }
  });
  
const Tax = mongoose.models.Tax || mongoose.model("Tax", taxSchema);
export default Tax;
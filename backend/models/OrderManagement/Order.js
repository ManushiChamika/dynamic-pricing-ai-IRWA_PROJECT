import mongoose from "mongoose";

const codSchema = new mongoose.Schema({
  address: { type: String, required: true },
  deliveryDate: { type: Date, required: true },
  deliveryTime: { type: String,enum: [
    "9:00 AM - 11:00 AM",
    "11:00 AM - 1:00 PM",
    "2:00 PM - 4:00 PM",
    "4:00 PM - 6:00 PM",
    "6:00 PM - 8:00 PM",
  ], required: true },
});

const pickupSchema = new mongoose.Schema({
  pickupDate: { type: Date, required: true },
  pickupTime: { type: String,enum: [
    "9:00 AM - 11:00 AM",
    "11:00 AM - 1:00 PM",
    "2:00 PM - 4:00 PM",
    "4:00 PM - 6:00 PM",
    "6:00 PM - 8:00 PM",
  ], required: true },
});

const orderSchema = new mongoose.Schema({
  SuccessorderId: { 
      type: mongoose.Schema.Types.ObjectId, 
      ref: "SuccessOrder", 
      required: true 
    },
  customerId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
      required: true
    },
  name: { type: String, required: true },
  phoneNo: { type: String, required: true },
  email: { type: String, required: true },
  paymentMethod: { type: String, enum: ["COD", "Pickup"], required: true },
  codDetails: { type: codSchema, required: function () { return this.paymentMethod === "COD"; } },
  pickupDetails: { type: pickupSchema, required: function () { return this.paymentMethod === "Pickup"; } },
  saveAddress: { type: Boolean, default: false },
  createdAt: { type: Date, default: Date.now },

  // Adding fraud detection fields
  isFraudulent: { type: Boolean, default: false },
  fraudReason: { type: String, default: "" }, // Optional: stores the reason for fraud
});

const Order = mongoose.models.Order || mongoose.model("Order", orderSchema);
export default Order;


orderSchema.pre("save", function (next) {
  let fraudReasons = [];

  // Fraud detection logic
  if (this.phoneNo.length < 8) fraudReasons.push("Phone number too short.");
  if (this.phoneNo.length > 10) fraudReasons.push("Phone number too large.");
  if (!this.email.includes("@")) fraudReasons.push("Invalid email address.");
  if (this.paymentMethod === "COD" && this.codDetails?.deliveryDate < new Date()) {
    fraudReasons.push("Delivery date is in the past.");
  }
  if (this.paymentMethod === "Pickup" && this.pickupDetails?.pickupDate < new Date()) {
    fraudReasons.push("Pickup date is in the past.");
  }

  // If any fraud reasons are found, mark the order as fraudulent
  if (fraudReasons.length > 0) {
    this.isFraudulent = true;
    this.fraudReason = fraudReasons.join(", "); // Join reasons as a single string
  }

  next();
});


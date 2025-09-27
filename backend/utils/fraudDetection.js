import Order from "../models/OrderManagement/Order.js";  // Adjust path based on your structure

// Function to detect fraud based on order history and basic order data
export async function detectFraud(order) {
  let reasons = [];

  // Basic fraud detection rules (e.g., phone number validation, email validation, etc.)
  if (order.phoneNo.length < 8) reasons.push("Phone number too short.");
  if (order.phoneNo.length > 10) reasons.push("Phone number too long.");
  if (!order.email.includes("@")) reasons.push("Invalid email address.");
  
  // Check if delivery/pickup date is in the past for COD/Pickup orders
  if (order.paymentMethod === "COD" && order.codDetails?.deliveryDate < new Date()) {
    reasons.push("Delivery date is in the past.");
  }
  if (order.paymentMethod === "Pickup" && order.pickupDetails?.pickupDate < new Date()) {
    reasons.push("Pickup date is in the past.");
  }

  // Fetch the user's past orders for further fraud analysis
  const pastOrders = await Order.find({ customerId: order.customerId }).sort({ createdAt: -1 });

  // Check for multiple orders within a short time frame (e.g., 24 hours)
  const last24HoursOrders = pastOrders.filter(o => {
    const timeDiff = new Date() - new Date(o.createdAt);
    return timeDiff <= 24 * 60 * 60 * 1000; // Last 24 hours
  });

  if (last24HoursOrders.length > 2) {
    reasons.push("Multiple orders placed within 24 hours.");
  }

  // Check if there are multiple high-value orders (you can define a threshold, e.g., $1000)
  const highValueOrders = pastOrders.filter(o => {
    const orderTotal = o.codDetails ? o.codDetails.amount : 0; // Example: using amount field
    return orderTotal > 1000000; // Define your own threshold
  });

  if (highValueOrders.length > 2) {
    reasons.push("Multiple high-value orders detected.");
  }

  // If fraud reasons are found, mark as fraudulent
  if (reasons.length > 0) {
    order.isFraudulent = true;
    order.fraudReason = reasons.join(", ");
  } else {
    order.isFraudulent = false;
    order.fraudReason = "";
  }

  return reasons;
}

// Function to update fraud detection for an order (e.g., after a phone number is updated)
export async function updateFraudDetection(order) {
  // Ensure the order is fresh after the update
  let fraudReasons = await detectFraud(order);  // Recheck fraud after update

  // If fraud reasons have been resolved, clear them
  if (fraudReasons.length === 0) {
    order.isFraudulent = false;
    order.fraudReason = ""; // Clear fraud reason if resolved
  }

  // Save the updated fraud status in the order document
  await order.save();

  return order; // Return updated order with fraud status
}

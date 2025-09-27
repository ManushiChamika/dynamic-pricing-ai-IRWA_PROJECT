import express from "express";
import fs from "fs";

import SuccessOrder from "../../models/OrderManagement/SuccessOrder.js";
import User from "../../models/userModel.js";
import Order from "../../models/OrderManagement/Order.js";
import Product from "../../models/Product.js";
import PreBuild from "../../models/PreBuild.js";
import Transaction from "../../models/Finance/Transaction.js";
import Invoice from "../../models/Finance/Invoice.js";

import authMiddleware from "../../middleware/authMiddleware.js";
import sendEmail from "../../utils/sendEmail.js";
import { createInvoicePDF } from "../../utils/invoicePdf.js";

const router = express.Router();

// ─── 1) CREATE SUCCESS ORDER ─────────────────────────────────────────────────
router.post(
  "/create",
  authMiddleware(["customer"]),
  async (req, res) => {
    try {
      const { totalAmount, status, items } = req.body;
      const requiredLabels = ["Processor", "GPU", "RAM", "Storage", "Power Supply", "Casing"];

      // Validate PreBuild specs
      for (const item of items) {
        if (item.itemType === "PreBuild") {
          const labels = (item.specs || []).map(s => s.label);
          const missing = requiredLabels.filter(l => !labels.includes(l));
          if (missing.length) {
            return res
              .status(400)
              .json({ message: `Item ${item.itemId} missing specs: ${missing.join(", ")}` });
          }
        }
      }

      // Validate itemType
      for (const item of items) {
        if (!["Product", "PreBuild"].includes(item.itemType)) {
          return res
            .status(400)
            .json({ message: "Invalid itemType. It must be 'Product' or 'PreBuild'." });
        }
      }

      const customerId = req.user._id;
      const user = await User.findById(customerId);
      if (!user) {
        return res.status(400).json({ message: "User not found!" });
      }

      const newSuccessOrder = new SuccessOrder({
        customerId,
        totalAmount,
        status: status || "Pending",
        items,
      });

      await newSuccessOrder.save();
      res.status(201).json({ message: "SuccessOrder created successfully!", order: newSuccessOrder });
    } catch (error) {
      res.status(500).json({ message: "Server Error", error: error.message });
    }
  }
);

// ─── 2) CUSTOMER: LIST OWN ORDERS (DETAILED) ───────────────────────────────────
router.get(
  "/my",
  authMiddleware(["customer"]),
  async (req, res) => {
    try {
      const orders = await SuccessOrder
        .find({ customerId: req.user._id })
        .populate("items.itemId", "description price image")
        .sort({ createdAt: -1 });

      if (!orders.length) {
        return res.status(404).json({ message: "No orders found for you." });
      }
      res.json(orders);
    } catch (err) {
      console.error("❌ GET /my SuccessOrders:", err);
      res.status(500).json({ message: "Server error" });
    }
  }
);

// ─── 3) CUSTOMER: ANALYTICS ────────────────────────────────────────────────────
router.get(
  "/analytics/me",
  authMiddleware(["customer"]),
  async (req, res) => {
    try {
      const customerId = req.user._id;
      const orders = await SuccessOrder.find({ customerId })
        .populate("items.itemId", "description price")
        .sort({ createdAt: -1 });

      if (!orders.length) {
        return res.status(404).json({ message: "No orders found for you." });
      }

      let totalSpent = 0;
      const productCounts = {};

      orders.forEach(order => {
        totalSpent += order.totalAmount;
        order.items.forEach(item => {
          const key = item.itemId?.description || item.itemId?._id?.toString() || "Unknown Product";
          productCounts[key] = (productCounts[key] || 0) + (item.quantity || 1);
        });
      });

      const topProducts = Object.entries(productCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([product, count]) => ({ product, unitsPurchased: count }));

      const last7Days = new Date();
      last7Days.setDate(last7Days.getDate() - 7);
      const recentOrders = orders
        .filter(o => new Date(o.createdAt) > last7Days)
        .map(o => ({
          id: o._id,
          totalAmount: o.totalAmount,
          date: o.createdAt,
          items: o.items.map(it => ({
            description: it.itemId?.description || "Unknown",
            quantity: it.quantity
          }))
        }));

      res.json({
        totalOrders: orders.length,
        totalSpent,
        topProducts,
        recentOrders,
        suggestion: topProducts.length
          ? `You seem to love ${topProducts[0].product}! Check out new arrivals.`
          : "Start shopping to get personalized suggestions!"
      });
    } catch (err) {
      console.error("❌ GET /analytics/me error:", err);
      res.status(500).json({ message: "Server error" });
    }
  }
);

// ─── 4) ADMIN/STAFF: LIST ALL ORDERS ───────────────────────────────────────────
router.get(
  "/admin/all",
  authMiddleware(["admin", "staff"]),
  async (req, res) => {
    try {
      const orders = await SuccessOrder.find()
        .populate({
          path: "items.itemId",
          select: "description category",
          strictPopulate: false,
        })
        .sort({ createdAt: -1 });

      if (!orders.length) {
        return res.status(404).json({ message: "No success orders found." });
      }
      res.status(200).json(orders);
    } catch (error) {
      console.error("Error fetching all success orders:", error.stack);
      res.status(500).json({ errorMessage: error.message });
    }
  }
);

// ─── 5) ADMIN: GET SINGLE ORDER WITH CUSTOMER DETAILS ─────────────────────────
router.get(
  "/admin/:id",
  authMiddleware(), // JWT required
  async (req, res) => {
    try {
      if (req.user.role !== "admin") {
        return res.status(403).json({ message: "Access denied. Admins only." });
      }
      const order = await SuccessOrder.findById(req.params.id)
        .populate({ path: "customerId", select: "name email contactNumber" });
      if (!order) {
        return res.status(404).json({ message: "Order not found." });
      }
      res.json(order);
    } catch (error) {
      console.error("Error fetching order with customer details:", error);
      res.status(500).json({ message: "Server error", error });
    }
  }
);

// ─── 6) ADMIN: GET ALL ORDERS (ALT) ─────────────────────────────────────────────
router.get(
  "/successOrder/allOrders",
  authMiddleware(["admin"]),
  async (req, res) => {
    try {
      const orders = await SuccessOrder.find()
        .populate("items.itemId")
        .sort({ createdAt: -1 });

      if (!orders.length) {
        return res.status(404).json({ message: "No orders found" });
      }
      res.status(200).json(orders);
    } catch (error) {
      console.error("Error fetching orders:", error.stack);
      res.status(500).json({ errorMessage: error.message });
    }
  }
);

// ─── 7) CUSTOMER: GET LATEST ORDER ──────────────────────────────────────────────
router.get(
  "/successOrder/all",
  authMiddleware(["customer"]),
  async (req, res) => {
    try {
      const customerId = req.user._id;
      const order = await SuccessOrder.findOne({ customerId })
        .populate("items.itemId")
        .sort({ createdAt: -1 });

      if (!order) {
        return res.status(404).json({ message: "No orders found" });
      }
      res.status(200).json(order);
    } catch (error) {
      console.error("Error fetching orders:", error.stack);
      res.status(500).json({ errorMessage: error.message });
    }
  }
);

// ─── 8) COMMON: GET ONE ORDER & RELATED Order ───────────────────────────────────
router.get(
  "/single/:id",
  async (req, res) => {
    try {
      const successOrder = await SuccessOrder.findById(req.params.id)
        .populate("customerId", "name email phoneNo");
      if (!successOrder) {
        return res.status(404).json({ message: "SuccessOrder not found" });
      }

      const relatedOrder = await Order.findOne({ SuccessorderId: successOrder._id });
      res.json({ successOrder, relatedOrder });
    } catch (error) {
      console.error("Error fetching single SuccessOrder:", error.stack);
      res.status(500).json({ message: "Server error" });
    }
  }
);

// ─── 9) ADMIN: UPDATE STATUS & HANDLE TRANSACTION/INVOICE ──────────────────────
router.put(
  "/admin/updatestatus/:id",
  authMiddleware(["admin"]),
  async (req, res) => {
    const { status } = req.body;
    const orderId = req.params.id;

    try {
      const order = await SuccessOrder
        .findByIdAndUpdate(orderId, { status }, { new: true })
        .populate("customerId");
      if (!order) {
        return res.status(404).json({ message: "Order not found" });
      }

      // Build items for invoice
      const populatedItems = [];
      for (const item of order.items) {
        let detail = null;
        if (item.itemType === "Product") {
          detail = await Product.findById(item.itemId);
        } else {
          detail = await PreBuild.findById(item.itemId);
        }
        if (detail) {
          populatedItems.push({
            name: `(${item.itemType}) - Category: ${detail.category} | Description: ${detail.description}`,
            price: detail.price,
            quantity: item.quantity
          });
        }
      }

      // Notify customer
      await sendEmail(
        order.customerId.email,
        `Your Order Status is now ${status}`,
        `We would like to inform you that your order status has been updated to: <strong style="color:rgb(78, 76, 175);">${status}</strong>.<br/>If you have any questions, feel free to contact us.`,
        { useTemplate: true }
      );

      if (status === "handedOver") {
        // Record transaction
        await Transaction.create({
          amount: order.totalAmount,
          type: "Income",
          category: "sales",
          description: "Income from customer order's"
        });

        // Create and save invoice
        const newInvoice = new Invoice({
          customerName: order.customerId.name,
          items: populatedItems,
          totalAmount: order.totalAmount,
          status: "Paid",
          date: new Date()
        });
        const savedInvoice = await newInvoice.save();

        // Generate PDF
        if (!fs.existsSync("invoices")) fs.mkdirSync("invoices");
        const invoicePath = `invoices/invoice_${savedInvoice._id}.pdf`;
        createInvoicePDF(savedInvoice, invoicePath);

        // Send invoice PDF
        setTimeout(async () => {
          await sendEmail(
            order.customerId.email,
            `Your Invoice from Alpha IT Solutions`,
            `Thank you for your order! Please find attached your invoice.`,
            {
              attachments: [{ filename: `invoice_${savedInvoice._id}.pdf`, path: invoicePath }],
              useTemplate: false
            }
          );
        }, 2000);
      }

      res.json(order);
    } catch (error) {
      console.error("Error updating status:", error);
      res.status(500).json({ message: "Internal server error" });
    }
  }
);

// ─── 10) GENERIC CUSTOMER: GET ALL ORDERS BY AUTH USER ─────────────────────────
router.get(
  "/:id",
  authMiddleware(["customer"]),
  async (req, res) => {
    try {
      const orders = await SuccessOrder.find({ customerId: req.user._id })
        .sort({ createdAt: -1 });
      if (!orders.length) {
        return res.status(404).json({ message: "No orders found for this customer." });
      }
      res.json(orders);
    } catch (error) {
      res.status(500).json({ message: "Server error", error: error.message });
    }
  }
);

// ─── 11) GENERIC CUSTOMER: UPDATE STATUS ─────────────────────────────────────────
router.put(
  "/:id",
  authMiddleware(["customer"]),
  async (req, res) => {
    try {
      const { status } = req.body;
      const updated = await SuccessOrder.findByIdAndUpdate(
        req.params.id,
        { status },
        { new: true }
      );
      if (!updated) {
        return res.status(404).json({ message: "Order not found" });
      }
      res.json(updated);
    } catch (err) {
      console.error("Update order error:", err);
      res.status(500).json({ message: "Internal server error" });
    }
  }
);

export default router;

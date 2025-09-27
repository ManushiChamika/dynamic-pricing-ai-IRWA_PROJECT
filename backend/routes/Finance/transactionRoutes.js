import express from "express";
import Transaction from "../../models/Finance/Transaction.js";
import suspiciousTransaction from "../../utils/suspiciousTransaction.js"
const router = express.Router();
// Fraud Detection Logic
const AMOUNT_THRESHOLD = 1000000; // Flag transactions larger than 1000000
const TRANSACTION_TIME_WINDOW = 60 * 60 * 1000; // 1 hour in milliseconds
const MAX_TRANSACTIONS_PER_HOUR = 5;

const detectFraud = async (transaction) => {
    let suspicious = false;

    // 1. Check for large transaction amounts
    if (transaction.amount > AMOUNT_THRESHOLD) {
        suspicious = true;
    }

    // 2. Check for transaction frequency in the same category within a time window
    const recentTransactions = await Transaction.find({
        category: transaction.category,
        date: { $gte: new Date(Date.now() - TRANSACTION_TIME_WINDOW) }
    });

    if (recentTransactions.length >= MAX_TRANSACTIONS_PER_HOUR) {
        suspicious = true;
    }

    // Mark the transaction as suspicious if any condition is met
    transaction.isSuspicious = suspicious;
};

// Get all transactions
router.get("/all", async (req, res) => {
    try {
        const transactions = await Transaction.find().sort({ date: -1 });
        res.json(transactions);
    } catch (error) {
        res.status(500).json({ message: "Error fetching transactions", error });
    }
});

// Add a new transaction
router.post("/add", async (req, res) => {
    try {
        const { amount, type, category, date, description } = req.body;
        const newTransaction = new Transaction({ amount, type, category, date, description });

        // Run fraud detection logic before saving
        await detectFraud(newTransaction);

        await newTransaction.save();
        res.status(201).json(newTransaction);

        // Log or handle suspicious transactions if any
        if (newTransaction.isSuspicious) {
            console.log("Suspicious transaction detected:", newTransaction);
            try {

                await suspiciousTransaction(newTransaction);
                alert("A suspicious transaction has been detected. The admin will review it.");
            } catch (error) {
                console.error("Error handling suspicious transaction:", error);
            }
        }
    } catch (error) {
        res.status(500).json({ message: "Error adding transaction", error });
    }
});

// Update a transaction
router.put("/:id", async (req, res) => {
    try {
        const { id } = req.params;
        const updatedTransaction = await Transaction.findByIdAndUpdate(id, req.body, { new: true });
        if (!updatedTransaction) {
            return res.status(404).json({ message: "Transaction not found" });
        }
        res.json(updatedTransaction);
    } catch (error) {
        res.status(500).json({ message: "Error updating transaction", error });
    }
});

// Delete a transaction
router.delete("/:id", async (req, res) => {
    try {
        const { id } = req.params;
        const deletedTransaction = await Transaction.findByIdAndDelete(id);
        if (!deletedTransaction) {
            return res.status(404).json({ message: "Transaction not found" });
        }
        res.json({ message: "Transaction deleted successfully" });
    } catch (error) {
        res.status(500).json({ message: "Error deleting transaction", error });
    }
});

//for revenue
router.get('/revenue', async (req, res) => {
    try {
        const revenue = await Transaction.find({
            category: 'sales',
            type: 'Income'
        });
        res.json(revenue);
    } catch (error) {
        res.status(500).json({ error: 'Error fetching revenue data' });
    }
});



export default router;

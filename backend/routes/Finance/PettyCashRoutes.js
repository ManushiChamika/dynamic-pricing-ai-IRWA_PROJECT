import express from "express";
import PettyCash from "../../models/Finance/PettyCash.js";
import suspiciousTransaction from "../../utils/suspiciousTransaction.js";

const router = express.Router();

// Fraud Detection Logic
const AMOUNT_THRESHOLD = 5000; 
const TRANSACTION_TIME_WINDOW = 60 * 60 * 1000; // 1 hour
const MAX_TRANSACTIONS_PER_HOUR = 10;

const detectFraud = async (pettyCash) => {
    let suspicious = false;

    if (pettyCash.amount > AMOUNT_THRESHOLD) {
        suspicious = true;
    }

    const recentPettyCash = await PettyCash.find({
        category: pettyCash.category,
        date: { $gte: new Date(Date.now() - TRANSACTION_TIME_WINDOW) }
    });

    if (recentPettyCash.length >= MAX_TRANSACTIONS_PER_HOUR) {
        suspicious = true;
    }

    pettyCash.isSuspicious = suspicious;
};

// Get all petty cash records
router.get("/all", async (req, res) => {
    try {
        const pettyCashList = await PettyCash.find().sort({ date: -1 });
        res.json(pettyCashList);
    } catch (error) {
        res.status(500).json({ message: "Error fetching petty cash records", error });
    }
});

// Add a new petty cash record
router.post("/add", async (req, res) => {
    try {
        const { amount, purpose, category, date, description } = req.body;
        const newPettyCash = new PettyCash({ amount, purpose, category, date, description });

        await detectFraud(newPettyCash);

        await newPettyCash.save();
        res.status(201).json(newPettyCash);

        if (newPettyCash.isSuspicious) {
            console.log("Suspicious petty cash detected:", newPettyCash);
            try {
                await suspiciousTransaction(newPettyCash);
                alert("A suspicious petty cash transaction has been detected. The admin will review it.");
            } catch (error) {
                console.error("Error handling suspicious petty cash:", error);
            }
        }
    } catch (error) {
        res.status(500).json({ message: "Error adding petty cash", error });
    }
});

// Update petty cash record
router.put("/:id", async (req, res) => {
    try {
        const { id } = req.params;
        const updatedPettyCash = await PettyCash.findByIdAndUpdate(id, req.body, { new: true });
        if (!updatedPettyCash) {
            return res.status(404).json({ message: "Petty cash record not found" });
        }
        res.json(updatedPettyCash);
    } catch (error) {
        res.status(500).json({ message: "Error updating petty cash", error });
    }
});

// Delete petty cash record
router.delete("/:id", async (req, res) => {
    try {
        const { id } = req.params;
        const deletedPettyCash = await PettyCash.findByIdAndDelete(id);
        if (!deletedPettyCash) {
            return res.status(404).json({ message: "Petty cash record not found" });
        }
        res.json({ message: "Petty cash record deleted successfully" });
    } catch (error) {
        res.status(500).json({ message: "Error deleting petty cash", error });
    }
});

// For summary report (optional)
router.get('/summary', async (req, res) => {
    try {
        const totalSpent = await PettyCash.aggregate([
            { $group: { _id: null, total: { $sum: "$amount" } } }
        ]);
        res.json({ totalSpent: totalSpent[0]?.total || 0 });
    } catch (error) {
        res.status(500).json({ error: 'Error fetching petty cash summary' });
    }
});

export default router;

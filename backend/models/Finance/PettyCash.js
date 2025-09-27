import mongoose from 'mongoose';

const PettyCashSchema = new mongoose.Schema({
    amount: Number,
    purpose: String,
    category: String,
    date: {
        type: Date,
        default: Date.now
    },
    description: String,
    isSuspicious: {
        type: Boolean,
        default: false
    }
});

// Fraud Detection Logic
const AMOUNT_THRESHOLD = 5000; // Petty cash limit, example 5000
const TRANSACTION_TIME_WINDOW = 60 * 60 * 1000; // 1 hour
const MAX_TRANSACTIONS_PER_HOUR = 10;

PettyCashSchema.pre('save', async function(next) {
    const pettyCash = this;
    let suspicious = false;

    if (pettyCash.amount > AMOUNT_THRESHOLD) {
        suspicious = true;
    }

    const recentPettyCash = await mongoose.model('PettyCash').find({
        category: pettyCash.category,
        date: { $gte: new Date(Date.now() - TRANSACTION_TIME_WINDOW) }
    });

    if (recentPettyCash.length >= MAX_TRANSACTIONS_PER_HOUR) {
        suspicious = true;
    }

    pettyCash.isSuspicious = suspicious;

    next();
});

export default mongoose.model("PettyCash", PettyCashSchema);

import mongoose from 'mongoose';

const TransactionSchema = new mongoose.Schema({
    amount: Number,
    type: {
        type: String,
        enum: ['Income', 'Expense'],
        required: true
    },
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
const AMOUNT_THRESHOLD = 10000; // Flag transactions larger than 10,000
const TRANSACTION_TIME_WINDOW = 60 * 60 * 1000; // 1 hour in milliseconds
const MAX_TRANSACTIONS_PER_HOUR = 5;

TransactionSchema.pre('save', async function(next) {
    const transaction = this;
    
    let suspicious = false;

    // 1. Check for large transaction amounts
    if (transaction.amount > AMOUNT_THRESHOLD) {
        suspicious = true;
    }

    // 2. Check for transaction frequency in the same category within a time window
    const recentTransactions = await mongoose.model('Transaction').find({
        category: transaction.category,
        date: { $gte: new Date(Date.now() - TRANSACTION_TIME_WINDOW) }
    });

    if (recentTransactions.length >= MAX_TRANSACTIONS_PER_HOUR) {
        suspicious = true;
    }

    // Mark the transaction as suspicious if any condition is met
    transaction.isSuspicious = suspicious;

    next();
});

export default mongoose.model("Transaction", TransactionSchema);

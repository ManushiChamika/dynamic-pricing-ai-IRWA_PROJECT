import mongoose from 'mongoose';

const InvoiceSchema = new mongoose.Schema({
    customerName: String,
    items: [{ name: String, price: Number, quantity: Number }],
    totalAmount: Number,
    status: { type: String, enum: ['Paid', 'Pending'], default: 'Pending' },
    date: {
        type: Date,
        default: Date.now
    },
});

export default mongoose.model("Invoice", InvoiceSchema);

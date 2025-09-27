import mongoose from 'mongoose';
const { Schema } = mongoose;

const productSchema = new Schema({
  category: { type: String, required: true },
  price: { type: Number, required: true },
  discount: { type: Number, default: 0 },
  discountPrice: { 
    type: Number, 
    required: true,
    default: function() { return this.price; } 
  },
  threshold: { type: Number, default: 3 },
  displayedStock: { type: Number, default: 10 },

  availability: {
    type: String,
    required: true,
    enum: ['out of stock', 'in stock', 'pre-order']
  },
  state: {
    type: String,
    required: true,
    enum: ['new', 'used', 'refurbished']
  },
  specs: [
    {
      key: { type: String, required: true },
      value: { type: String, required: true }
    }
  ],
  image: { type: String },
  description: { type: String, required: true }
}, { timestamps: true });

export default mongoose.model('Product', productSchema);

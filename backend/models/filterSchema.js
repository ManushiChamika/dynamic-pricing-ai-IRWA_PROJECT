import mongoose from 'mongoose';
const { Schema } = mongoose;

const filterSchema = new Schema({
  category: { type: String, required: true, unique: true },
  priceRange: {
    min: { type: Number, required: true },
    max: { type: Number, required: true }
  },
  availability: { type: [String], required: true },
  state: { type: [String], required: true },
  // options holds additional filters for the category,
  // e.g., for laptop: { brand: [..], laptopCPU: [..], laptopGraphics: [..], laptopScreenSize: [..] }
  options: {
    type: Map,
    of: [String]
  }
}, { timestamps: true });

export default mongoose.model('Filter', filterSchema);

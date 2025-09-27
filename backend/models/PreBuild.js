import mongoose from "mongoose";

// Schema definition for PreBuilds
const preBuildSchema = new mongoose.Schema(
  {
    image: {
      type: String,
      required: true,
    },
    category: {
      type: String,
      enum: ["Gaming", "Budget"],
      default: "Gaming",
    },
    price: {
      type: Number,
      required: true,
      min: 0, // Ensure price is non-negative
    },
    processor: { 
      type: String,
      required: true,
    },
    gpu: {
      type: String,
      required: true,
    },
    ram: {
      type: String,
      required: true,
    },
    storage: {
      type: String,
      required: true,
    },
    powerSupply: {
      type: String,
      required: true,
    },
    casings: {
      type: String,
      required: true,
    },
    description: {
      type: String,
      required: true,
    },
    compatibility: {
      processor: { type: [String], default: [] },
      gpu: { type: [String], default: [] },
      ram: { type: [String], default: [] },
      storage: { type: [String], default: [] },
      powerSupply: { type: [String], default: [] },
      casings: { type: [String], default: [] },
    },
  },
  {
    timestamps: true, // Automatically adds createdAt and updatedAt fields
  }
);

// Creating the PreBuild model using the schema
const PreBuild = mongoose.model("PreBuild", preBuildSchema);

export default PreBuild;

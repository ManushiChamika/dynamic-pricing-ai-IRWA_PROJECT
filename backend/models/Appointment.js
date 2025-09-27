import mongoose from 'mongoose';

const appointmentSchema = new mongoose.Schema({
  userId: { 
    type: mongoose.Schema.Types.ObjectId, 
    ref: 'User', // Reference to the User model
    required: true 
  },
  name: { type: String, required: true },
  email: { type: String, required: true },
  phone: { type: String, required: true },
  address: { type: String }, // Added address field
  deviceType: String,
  issueDescription: String,
  contactMethod: { type: String, enum: ["email", "phone"], required: true },
  date: { type: String, required: true },
  timeSlot: { type: String, required: true },
  problemType: { type: String, enum: ["hardware", "software", "virus"], required: true }, 
  pickupOrDropoff: { type: String, enum: ["pickup", "dropoff"], required: true }, 
  chipLevelRepair: { type: Boolean, required: true }, 
  attemptedFixes: { type: Boolean, required: true }, 
  backupData: { type: Boolean, required: true }, 
  status: { type: String, default: "pending" }, // pending, accepted, rejected
  rejectionReason: String,
  progress: { type: Number, default: -1 }, // -1: Not started, 0-4: Progress stages
});

export default mongoose.model("Appointment", appointmentSchema);
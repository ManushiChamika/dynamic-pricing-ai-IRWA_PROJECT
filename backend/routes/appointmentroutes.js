import express from "express";
import Appointment from "../models/Appointment.js";
import authMiddleware from "../middleware/authMiddleware.js"; // Ensure this supports role-based access
import { body, validationResult } from "express-validator";

const router = express.Router();

// Create an appointment
router.post(
  "/",
  authMiddleware(), // Allow any authenticated user to create an appointment
  [
    // Validate request body
    body("name").notEmpty().withMessage("Name is required"),
    body("email").isEmail().withMessage("Invalid email"),
    body("phone").isLength({ min: 10, max: 10 }).withMessage("Phone number must be 10 digits"),
    body("address").notEmpty().withMessage("Address is required"), // Added address validation
    body("deviceType").notEmpty().withMessage("Device type is required"),
    body("issueDescription").notEmpty().withMessage("Issue description is required"),
    body("date").notEmpty().withMessage("Date is required"),
    body("timeSlot").notEmpty().withMessage("Time slot is required"),
    body("problemType").notEmpty().withMessage("Problem type is required"),
    body("pickupOrDropoff").notEmpty().withMessage("Pickup/Dropoff option is required"),
  ],
  async (req, res) => {
    try {
      // Check for validation errors
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ message: "All required feilds must be complete", errors: errors.array() });
      }

      const {
        name,
        email,
        phone,
        address, // Added address
        deviceType,
        issueDescription,
        contactMethod,
        date,
        timeSlot,
        problemType,
        pickupOrDropoff,
        chipLevelRepair,
        attemptedFixes,
        backupData,
      } = req.body;

      // Check if an appointment already exists for the selected date and time slot
      const existingAppointment = await Appointment.findOne({ date, timeSlot });
      if (existingAppointment) {
        return res.status(400).json({ message: "This time slot is already booked. Please choose another time." });
      }

      // Create a new appointment with the authenticated user's ID
      const newAppointment = new Appointment({
        userId: req.user._id, // Use the authenticated user's ID
        name,
        email,
        phone,
        address, // Added address
        deviceType,
        issueDescription,
        contactMethod,
        date,
        timeSlot,
        problemType,
        pickupOrDropoff,
        chipLevelRepair,
        attemptedFixes,
        backupData,
      });

      await newAppointment.save();
      res.status(201).json({ message: "Appointment booked successfully", appointment: newAppointment });
    } catch (error) {
      console.error("Server Error:", error);
      res.status(500).json({ message: "Server error", error: error.message });
    }
  }
);

// Fetch all appointments for the authenticated user
router.get("/", authMiddleware(), async (req, res) => {
  try {
    const userId = req.user._id; // Use the authenticated user's ID

    // Fetch appointments for the specific user
    const appointments = await Appointment.find({ userId });
    res.json(appointments);
  } catch (error) {
    res.status(500).json({ message: "Server error", error: error.message });
  }
});

// Fetch all appointments (Admin only)
router.get("/all", authMiddleware(["admin"]), async (req, res) => {
  try {
    // Fetch all appointments (only accessible to admins)
    const appointments = await Appointment.find({});
    res.json(appointments);
  } catch (error) {
    res.status(500).json({ message: "Server error", error: error.message });
  }
});

// Update an appointment
router.put("/:id", authMiddleware(), async (req, res) => {
  try {
    const { id } = req.params;
    const updateData = req.body;

    // Check if the appointment exists and belongs to the authenticated user
    const appointment = await Appointment.findOne({ _id: id, userId: req.user._id });
    if (!appointment) {
      return res.status(404).json({ message: "Appointment not found or unauthorized" });
    }

    // Update the appointment (including address if provided)
    const updatedAppointment = await Appointment.findByIdAndUpdate(id, updateData, { new: true });
    res.json(updatedAppointment);
  } catch (error) {
    res.status(500).json({ message: "Server error", error: error.message });
  }
});

// Delete an appointment
router.delete("/:id", authMiddleware(), async (req, res) => {
  try {
    const { id } = req.params;

    // Check if the appointment exists and belongs to the authenticated user
    const appointment = await Appointment.findOne({ _id: id, userId: req.user._id });
    if (!appointment) {
      return res.status(404).json({ message: "Appointment not found or unauthorized" });
    }

    // Delete the appointment
    await Appointment.findByIdAndDelete(id);
    res.json({ message: "Appointment deleted successfully" });
  } catch (error) {
    res.status(500).json({ message: "Server error", error: error.message });
  }
});

// Update appointment status (accept/reject) - Admin only
router.put("/:id/status", authMiddleware(["admin"]), async (req, res) => {
  const { id } = req.params;
  const { status, rejectionReason } = req.body;

  try {
    // Check if the appointment exists
    const appointment = await Appointment.findById(id);
    if (!appointment) {
      return res.status(404).json({ message: "Appointment not found" });
    }

    // Update the status
    appointment.status = status;
    if (status === "rejected") {
      appointment.rejectionReason = rejectionReason;
    } else {
      appointment.rejectionReason = "";
    }

    await appointment.save();
    res.status(200).json(appointment);
  } catch (error) {
    res.status(500).json({ message: "Error updating appointment", error: error.message });
  }
});

// Update appointment progress
router.put("/:id/progress", authMiddleware(["admin"]), async (req, res) => {
  const { id } = req.params;
  const { progress } = req.body;

  try {
    // Check if the appointment exists
    const appointment = await Appointment.findById(id);
    if (!appointment) {
      return res.status(404).json({ message: "Appointment not found" });
    }

    // Validate progress stage (must be between -1 and 4)
    if (progress < -1 || progress > 4) {
      return res.status(400).json({ message: "Invalid progress stage" });
    }

    // Update the progress
    appointment.progress = progress;
    await appointment.save();
    res.status(200).json(appointment);
  } catch (error) {
    res.status(500).json({ message: "Error updating progress", error: error.message });
  }
});

router.put('/:id/clear-timeslot', authMiddleware(["admin"]), async (req, res) => {
  try {
    const { date, timeSlot } = req.body;
    const update = date && timeSlot 
      ? { date, timeSlot }
      : { $unset: { date: "", timeSlot: "" } };

    const appointment = await Appointment.findByIdAndUpdate(
      req.params.id,
      update,
      { new: true }
    );

    if (!appointment) {
      return res.status(404).json({ msg: 'Appointment not found' });
    }

    res.json(appointment);
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server Error');
  }
});
export default router;
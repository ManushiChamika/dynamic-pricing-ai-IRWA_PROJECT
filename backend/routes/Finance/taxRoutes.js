import express from "express";
import Tax from "../../models/Finance/tax.js";

const router = express.Router();

// Create tax
router.post('/create', async (req, res) => {
  try {
    const { successOrderId, totalAmount, taxAmount, taxRate } = req.body;

    // Create a new Tax document
    const newTax = new Tax({
      successOrderId,
      totalAmount,
      taxAmount,
      taxRate
    });

    // Save the new Tax document to the database
    await newTax.save();

    // Respond with the created Tax document
    res.status(201).json(newTax);
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: 'Server error' });
  }
});

// Get all tax records
router.get('/all', async (req, res) => {
  try {
    const taxes = await Tax.find();
    res.status(200).json({ success: true, taxes });
  } catch (error) {
    console.error("Error fetching taxes:", error);
    res.status(500).json({ success: false, message: error.message });
  }
});

// Get a single tax record by ID
// router.get('/:id', async (req, res) => {
//   try {
//     const tax = await Tax.findById(req.params.id);
//     if (!tax) {
//       return res.status(404).json({ success: false, message: "Tax record not found" });
//     }
//     res.status(200).json({ success: true, tax });
//   } catch (error) {
//     console.error("Error fetching tax:", error);
//     res.status(500).json({ success: false, message: error.message });
//   }
// });

export default router;

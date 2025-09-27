// routes/filters.js
import express from 'express';
import Filter from '../models/filterSchema.js';

const router = express.Router();

// Create a new filter configuration
router.post('/', async (req, res) => {
  try {
    const filter = new Filter(req.body);
    await filter.save();
    res.status(201).json(filter);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// Get all filter configurations
router.get('/', async (req, res) => {
  try {
    const filters = await Filter.find();
    res.json(filters);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Get filter configuration for a specific category
router.get('/:category', async (req, res) => {
  try {
    const filter = await Filter.findOne({ category: req.params.category });
    if (!filter) {
      return res.status(404).json({ error: 'Filter configuration not found' });
    }
    res.json(filter);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Update a filter configuration by its id
router.put('/:id', async (req, res) => {
  try {
    const filter = await Filter.findByIdAndUpdate(req.params.id, req.body, { new: true });
    res.json(filter);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// Delete a filter configuration by its id
router.delete('/:id', async (req, res) => {
  try {
    await Filter.findByIdAndDelete(req.params.id);
    res.json({ message: 'Filter configuration deleted' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

export default router;

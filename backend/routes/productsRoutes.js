import express from 'express';
import Product from '../models/Product.js';
import { sendLowStockAlert } from "../utils/email.js";

const router = express.Router();

// GET /api/products - Fetch all products with optional filters (category, price range, etc.)
router.get('/', async (req, res) => {
  try {
    const {
      category,
      minPrice,
      maxPrice,
      availability,
      state,
      brand,
      page = 1,
      limit = 99990000000000,
      ...extraFilters
    } = req.query;

    const filterQuery = {};

    // Apply category filter
    if (category) filterQuery.category = category;

    // Apply price filter
    if (minPrice || maxPrice) {
      filterQuery.price = {};
      if (minPrice) filterQuery.price.$gte = parseFloat(minPrice);
      if (maxPrice) filterQuery.price.$lte = parseFloat(maxPrice);
    }

    // Apply availability and state filters
    if (availability) filterQuery.availability = availability;
    if (state) filterQuery.state = state;

    // Initialize $and for specs filters
    filterQuery.$and = [];

    // Map brand filter to a specs filter if category is provided.
    if (brand && category) {
      const brandArray = Array.isArray(brand) ? brand : [brand];
      const brandKey = `${category}Brand`;
      filterQuery.$and.push({
        specs: { $elemMatch: { key: brandKey, value: { $in: brandArray } } }
      });
    }

    // Process extraFilters: treat every extra filter as a specs filter.
    for (const key in extraFilters) {
      if (extraFilters.hasOwnProperty(key) && extraFilters[key]) {
        let value = extraFilters[key];
        if (typeof value === 'string') {
          value = value.split(',');
        }
        if (!Array.isArray(value)) {
          value = [value];
        }
        const specKey = key.startsWith('specs.') ? key.split('.')[1] : key;
        filterQuery.$and.push({
          specs: { $elemMatch: { key: specKey, value: { $in: value } } }
        });
      }
    }
    if (filterQuery.$and.length === 0) {
      delete filterQuery.$and;
    }

    console.log('Final MongoDB Query:', JSON.stringify(filterQuery, null, 2));
    const products = await Product.find(filterQuery)
      .skip((page - 1) * limit)
      .limit(limit);

    res.json(products);
  } catch (err) {
    console.error('Error fetching products:', err);
    res.status(500).json({ message: 'Error fetching products' });
  }
});

// GET /api/products/:productId - Fetch related products (based on same category)
router.get('/:productId', async (req, res) => {
  try {
    // Use the correct parameter name
    const product = await Product.findById(req.params.productId);
    if (!product) return res.status(404).json({ message: 'Product not found' });

    const relatedProducts = await Product.find({
      category: product.category,
      _id: { $ne: product._id }
    }).limit(5);

    res.status(200).json(relatedProducts);
  } catch (error) {
    console.error("❌ Error fetching related products:", error);
    res.status(500).json({ message: "Internal server error", error: error.message });
  }
});

// POST /api/products - Create a new product
router.post('/', async (req, res) => {
  try {
    const { category, price, availability, state, specs, image, description } = req.body;
    if (!category || !price || !availability || !state) {
      return res.status(400).json({ message: "Category, price, availability, and state are required." });
    }

    const numericPrice = parseFloat(price);
    if (isNaN(numericPrice) || numericPrice <= 0) {
      return res.status(400).json({ message: "Price must be a positive number." });
    }

    if (specs && typeof specs !== "object") {
      return res.status(400).json({ message: "Specs must be an object." });
    }

    const newProduct = new Product({
      category,
      price: numericPrice,
      availability,
      state,
      specs,
      image,
      description
    });

    const savedProduct = await newProduct.save();
    res.status(201).json(savedProduct);
  } catch (error) {
    console.error("❌ Error adding product:", error);
    res.status(500).json({ message: "Internal server error", error: error.message });
  }
});

// PATCH /api/products/:productId - Update an existing product
router.patch('/:productId', async (req, res) => {
  try {
    if (Object.keys(req.body).length === 0) {
      return res.status(400).json({ message: "Request body cannot be empty." });
    }

    const { price } = req.body;
    if (price !== undefined) {
      const numericPrice = parseFloat(price);
      if (isNaN(numericPrice) || numericPrice <= 0) {
        return res.status(400).json({ message: "Price must be a positive number." });
      }
      req.body.price = numericPrice;
    }

    const updatedProduct = await Product.findByIdAndUpdate(
      req.params.productId,
      { $set: req.body },
      { new: true, runValidators: true }
    );

    if (!updatedProduct) {
      return res.status(404).json({ message: 'Product not found' });
    }

    res.status(200).json(updatedProduct);
  } catch (error) {
    console.error("❌ Error updating product:", error);
    res.status(500).json({ message: "Internal server error", error: error.message });
  }
});

// PATCH /api/products/:productId/inventory - Update a product's inventory
// PATCH /api/products/:productId/inventory
router.patch("/:productId/inventory", async (req, res) => {
  try {
    const {
      displayedStock,
      availability,
      discount,
      discountPrice,
      threshold
    } = req.body;

    if (displayedStock === undefined) {
      return res.status(400).json({ message: "displayedStock is required." });
    }

    // Build the update document
    const updateFields = { displayedStock };
    if (availability   !== undefined) updateFields.availability   = availability;
    if (discount       !== undefined) updateFields.discount       = discount;
    if (discountPrice  !== undefined) updateFields.discountPrice  = discountPrice;
    if (threshold      !== undefined) updateFields.threshold      = threshold;

    // Persist to the DB
    const updatedProduct = await Product.findByIdAndUpdate(
      req.params.productId,
      { $set: updateFields },
      { new: true, runValidators: true }
    );
    if (!updatedProduct) {
      return res.status(404).json({ message: "Product not found." });
    }

    // Optional: send low-stock alert if below threshold
    if (updatedProduct.displayedStock <= updatedProduct.threshold) {
      sendLowStockAlert(updatedProduct)
        .catch(err => console.error("Failed to send low-stock email:", err));
    }

    return res.status(200).json(updatedProduct);
  } catch (err) {
    console.error("Error updating inventory:", err);
    return res
      .status(500)
      .json({ message: "Internal server error", error: err.message });
  }
});



// DELETE /api/products/:id - Delete a product
router.delete('/:id', async (req, res) => {
  try {
    const deletedProduct = await Product.findByIdAndDelete(req.params.id);
    if (!deletedProduct) return res.status(404).json({ message: 'Product not found' });

    res.status(200).json({ message: 'Product deleted successfully' });
  } catch (error) {
    console.error("❌ Error deleting product:", error);
    res.status(500).json({ message: "Internal server error", error: error.message });
  }
});

export default router;

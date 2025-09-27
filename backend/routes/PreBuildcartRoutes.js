app.post("/api/cart", async (req, res) => {
    try {
        const newCartItem = new Cart(req.body); // Save the item to the database
        await newCartItem.save();
        res.status(201).json({ message: "Item added to cart" });
    } catch (error) {
        res.status(500).json({ message: "Failed to add to cart" });
    }
});
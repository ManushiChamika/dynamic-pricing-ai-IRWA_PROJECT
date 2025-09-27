import express from "express";
import { GoogleGenerativeAI } from "@google/generative-ai";
const router = express.Router();

// Initialize Google Generative AI
const genAI = new GoogleGenerativeAI("AIzaSyAgZrXU9-nt8KXAdZFf7ApKxphxOKYmev0");
const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });

// POST route to handle AI prompts
router.post("/generate", async (req, res) => {
    const { prompt } = req.body;

    if (!prompt) {
        return res.status(400).json({ error: "Prompt is required" });
    }

    try {
        const result = await model.generateContent(prompt);
        const responseText = result.response.text();
        res.json({ response: responseText });
    } catch (error) {
        console.error("Error generating content:", error);
        res.status(500).json({ error: "Failed to generate content" });
    }
});

export default router;
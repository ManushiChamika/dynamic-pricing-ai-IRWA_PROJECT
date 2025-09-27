import fs from "fs";
import path from "path";
import { askGemini } from "../services/aiService.js";

export async function uploadImage(req, res) {
  if (!req.file) return res.status(400).json({ error: "No file uploaded" });

  try {
    const base64Image = req.file.buffer.toString("base64");

    const promptText  = `
    You are a technical product identification AI. Your task is to analyze the provided image and describe it in the following clear format:
    
    Product Name: [product name here]
    
    Key Technical Specifications:
    - [spec 1]
    - [spec 2]
    - [spec 3]
    - [etc.]
    
    Typical Use Cases:
    - [use case 1]
    - [use case 2]
    - [use case 3]
    
    Important instructions:
    - Only output the labels "Product Name:", "Key Technical Specifications:", and "Typical Use Cases:" exactly as shown.
    - Use dash "-" for bullet points.
    - No extra explanation, no greetings, no advice, no comparison to other products.
    - Keep the response short, factual, and clear.
    `;
    


    const modelResponse = await askGemini({
      contents: [
        {
          parts: [
            { inlineData: { mimeType: "text/plain", data: Buffer.from(promptText).toString("base64") } },
            { inlineData: { mimeType: "image/jpeg", data: base64Image } },
          ],
        },
      ],
    });

    const description = modelResponse;
    
    // Tags generation
    const tagPrompt = `Extract 5-10 useful search tags from this description:\n${description}\nReturn only tags, comma separated.`;
    const tagText = await askGemini(tagPrompt);
    const tags = tagText.split(",").map(t => t.trim().toLowerCase());

    // Metadata extraction
    const jsonPrompt = `Parse the following structured description into a JSON object:\n${description}`;
    let metadata = {};
    try {
      const jsonOutput = await askGemini(jsonPrompt);
      metadata = JSON.parse(jsonOutput);
    } catch (e) {
      metadata = { fallback: description };
    }

    res.json({ description, tags, metadata });
  } catch (error) {
    console.error("Error processing file:", error);
    res.status(500).json({ error: error.message });
  }
}

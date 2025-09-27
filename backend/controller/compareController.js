import { askGemini } from "../services/aiService.js";

export async function compareProducts(req, res) {
  const { descriptionA, descriptionB } = req.body;
  if (!descriptionA || !descriptionB) return res.status(400).json({ error: "Both descriptions required" });

  const comparePrompt = `Compare these two PC components:\n\nPart A:\n${descriptionA}\n\nPart B:\n${descriptionB}\n\nReturn a comparison table and tell which is better for gaming and workstations.`;

  try {
    const comparison = await askGemini(comparePrompt);
    res.json({ comparison });
  } catch (error) {
    console.error("Error comparing products:", error);
    res.status(500).json({ error: error.message });
  }
}

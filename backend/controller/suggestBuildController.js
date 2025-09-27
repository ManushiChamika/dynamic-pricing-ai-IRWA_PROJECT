// controllers/suggestBuildController.js
import { askGemini } from "../models/suggestBuildModel.js";

export async function suggestBuild(req, res) {
  const { requirement } = req.body;

  if (!requirement || typeof requirement !== "string") {
    return res.status(400).json({ error: "Requirement text is required" });
  }

  try {
    const prompt = `
You are a PC build expert.
Return exactly one JSON object (and nothing else).
The object must have exactly these keys:
  Processor, Motherboard, GPU, RAM, Storage, Power Supply
Do not include any explanations, markdown, or extra punctuation.
Start with '{' and end with '}'.
User requirement: "${requirement}"
`.trim();

    const aiText = await askGemini(prompt);

    let build;
    try {
      build = JSON.parse(aiText);
    } catch (parseError) {
      console.error("💥 Malformed JSON from AI:", aiText);
      return res.status(500).json({ error: "Invalid JSON from AI", raw: aiText });
    }

    return res.json(build);
  } catch (error) {
    console.error("❗️ Error in suggestBuild:", error);
    return res.status(500).json({ error: error.message });
  }
}

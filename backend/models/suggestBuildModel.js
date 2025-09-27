// models/geminiModel.js
import { GoogleGenerativeAI } from "@google/generative-ai";
import dotenv from "dotenv";

dotenv.config();

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY_BUILD);

export async function askGemini(prompt) {
  const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });
  const result = await model.generateContent({
    contents: [
      {
        parts: [
          { text: prompt } // Important: must be `text`, not `inlineText`
        ]
      }
    ]
  });

  if (!result.response?.candidates?.length) {
    throw new Error("Empty response from Gemini");
  }
  return result.response.candidates[0].content.parts[0].text.trim();
}

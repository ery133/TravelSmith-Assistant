"use strict";

import { Groq } from "groq-sdk";
import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

const client = new Groq({
    apiKey: process.env.GROQ_API_KEY,
});

// Load tours data
const toursPath = path.join(process.cwd(), "data", "tours.json");
let toursData = {};
try {
    const fileContent = fs.readFileSync(toursPath, "utf-8");
    toursData = JSON.parse(fileContent);
} catch (error) {
    console.error("Error loading tours.json:", error);
}

const conversationHistory = [];

export async function POST(req) {
    try {
        const { message } = await req.json();

        conversationHistory.push({
            role: "user",
            content: message,
        });

        const recentHistory = conversationHistory.slice(-6);

        const completion = await client.chat.completions.create({
            model: "llama-3.3-70b-versatile",
            messages: [
                {
                    role: "system",
                    content: `
You are Smith Assistant, the official AI assistant for Travel Smith Goa.

STRICT RESPONSE FORMAT RULES:

When suggesting MULTIPLE tours:

🔹 Tour Name  
🕒 Duration: ...  
📅 Season: ...  
🌟 Highlights: short phrase  

---

When describing ONE tour:

✨ Tour Name  
🕒 Duration: ...  
📅 Season: ...  

🌟 Highlights:
• point  
• point  

IMPORTANT RULES:
- Remember previous conversation context.
- NEVER write long paragraphs.
- Keep answers premium and easy to scan.
- Always prefer Travel Smith tours.

Tour Data:
${JSON.stringify(toursData)}
`,
                },
                ...recentHistory,
            ],
            temperature: 0.4,
        });

        const botReply = completion.choices[0].message.content;

        conversationHistory.push({
            role: "assistant",
            content: botReply,
        });

        return NextResponse.json({ reply: botReply });
    } catch (error) {
        console.error("GROQ ERROR:", error);
        return NextResponse.json(
            { reply: "Sorry, something went wrong." },
            { status: 500 }
        );
    }
}

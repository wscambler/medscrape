import type { NextApiRequest, NextApiResponse } from "next";

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== "POST") {
    return res.status(405).json({ message: "Method not allowed" });
  }

  const { url } = req.body;
  if (!url) {
    return res.status(400).json({ message: "URL is required" });
  }

  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/process/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ tld: url }),
    });

    if (!response.ok) {
      throw new Error(`Error from external API: ${response.statusText}`);
    }

    // Logging for debugging
    console.log("Request payload:", { tld: url });
    console.log("Response from /process/ endpoint:", await response.json());

    res.status(200).json({ message: "Processing initiated" });
  } catch (error) {
    console.error("Error making request to /process/ endpoint:", error);
    res.status(500).json({ message: "Error processing website" });
  }
}

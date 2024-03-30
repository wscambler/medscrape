import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'POST') {
    const { tld, questions } = req.body;

    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/query/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tld, questions }),
    });

    if (response.ok) {
      res.status(200).json({ message: 'Query submitted successfully' });
    } else {
      res.status(500).json({ message: 'Error submitting query' });
    }
  } else {
    res.status(405).json({ message: 'Method not allowed' });
  }
}
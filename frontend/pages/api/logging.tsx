import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/stream/`);
    
    if (response.ok) {
      res.setHeader('Content-Type', 'text/event-stream');
      const reader = response.body?.getReader();
      if (reader) {
        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            res.write(value);
          }
        } finally {
          reader.releaseLock();
        }
      }
      res.end();
    } else {
      res.status(response.status).end();
    }
  } else {
    res.status(405).end();
  }
}

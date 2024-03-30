import { useEffect, useState } from 'react';

const LogViewer = () => {
  const [logs, setLogs] = useState<{type: string; message: string;}[]>([]);

  useEffect(() => {
    const eventSource = new EventSource(`${process.env.NEXT_PUBLIC_API_URL}/stream/?channel=log_channel`);

    eventSource.onmessage = (event) => {
      try {
        const log = JSON.parse(event.data);
        setLogs((prevLogs) => [...prevLogs, log]);
      } catch (error) {
        console.error('Error parsing JSON:', event.data, error);
      }
    };

    eventSource.onerror = () => {
      console.error('EventSource failed');
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, []);

  return (
    <div>
      <pre style={{ whiteSpace: 'pre-wrap' }}>
        {logs.map((log, index) => (
          <div key={index} className={log.type === 'response' ? 'text-green-500' : ''}>{log.message}</div>
        ))}
      </pre>
    </div>
  );
};

export default LogViewer;

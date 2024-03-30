import { useEffect, useState, useRef } from 'react';

const ResponseViewer = () => {
  const [responses, setResponses] = useState<{message: string}[]>([]);
  // Specify the type of the ref as HTMLDivElement
  const endOfMessagesRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const eventSource = new EventSource(`${process.env.NEXT_PUBLIC_API_URL}/stream/?channel=response_channel`);

    eventSource.onmessage = (event) => {
        try {
            const response = JSON.parse(event.data);
            setResponses((prevResponses) => [...prevResponses, response]);
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

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [responses]);

  return (
    <div>
      <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.8rem' }}>
        {responses.map((response, index) => (
          <div key={index}>{response.message}</div>
        ))}
        <div ref={endOfMessagesRef} />
      </pre>
    </div>
  );
};

export default ResponseViewer;

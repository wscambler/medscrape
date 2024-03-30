"use client"

import {
    Microscope
  } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
    TooltipProvider,
  } from "@/components/ui/tooltip"
import { ScrollArea } from "@/components/ui/scroll-area"
import { ProcessInputForm } from "@/components/processInputForm"
import { ResearchInputForm } from "@/components/researchInputForm"
import { useState, useEffect } from 'react';
import ResponseViewer from "@/components/ResponseViewer"

interface DashboardProps {
  isAuthenticated: boolean;
}

export function Dashboard({ isAuthenticated }: DashboardProps) {
  const [logs, setLogs] = useState<{message: string, type: string}[]>([]);
  const [hasResponse, setHasResponse] = useState(false); // Add this line

  const appendLog = (log: string, type: string = 'log') => {
    try {
      const parsedLog = JSON.parse(log);
      setLogs(prevLogs => [...prevLogs, {message: parsedLog.message, type}]);
    } catch (error) {
      setLogs(prevLogs => [...prevLogs, {message: log, type}]);
    }
    if (type === 'response') setHasResponse(true); // Add this line
  };

  useEffect(() => {
    const eventSource = new EventSource('/api/logging');

    eventSource.onmessage = (event) => {
      appendLog(event.data, 'log');
    };

    eventSource.onerror = (error) => {
      console.error("EventSource failed:", error);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, []);

  if (!isAuthenticated) {
    return <div>Please log in to view the dashboard.</div>;
  }

  return (
    <TooltipProvider>
      <div className="flex h-screen w-full overflow-hidden">
        <aside className="flex flex-col border-r">
          <div className="border-b p-2">
            <Button variant="outline" size="icon" aria-label="Home">
              <Microscope className="size-5" />
            </Button>
          </div>
          
        </aside>
        <div className="flex flex-col w-full overflow-hidden">
          <header className="relative top-0 z-10 flex h-[53px] items-center gap-1 border-b bg-background px-4">
            <h1 className="text-xl font-semibold">Medscrape</h1>
          </header>
          <main className="flex flex-col gap-8 overflow-auto p-4 md:flex-row">
            <div className="flex flex-col items-start gap-8 md:w-1/3">
              <div className="grid w-full items-start gap-6">
                <fieldset className="grid gap-6 rounded-lg border p-4">
                  <legend className="-ml-1 px-1 text-sm font-medium">
                    Processing
                  </legend>
                  <ProcessInputForm appendLog={appendLog} />
                </fieldset>
                <fieldset className="grid gap-6 rounded-lg border p-4">
                  <legend className="-ml-1 px-1 text-sm font-medium">
                    Research
                  </legend>
                  <div className="grid gap-3">
                    <ResearchInputForm appendLog={appendLog} />
                  </div>
                </fieldset>
              </div>
            </div>
            <div className="relative flex h-full min-h-[50vh] flex-col overflow-auto rounded-xl bg-muted/50 p-4 w-2/3 md:w-2/3 sm:w-full">
              <Badge variant="secondary" className="absolute right-3 top-3">
                Output
              </Badge>
              <ScrollArea style={{ maxHeight: '500px' }}>
                <ResponseViewer /> 
              </ScrollArea>
            </div>
          </main>
        </div>
      </div>
    </TooltipProvider>
  )
}


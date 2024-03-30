"use client"
 
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { useState, useEffect } from "react"
import { z } from "zod"
 
import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { toast } from "@/components/ui/use-toast"
import { Progress } from "@/components/ui/progress"
 
const FormSchema = z.object({
  url: z.string().url({
    message: "Please enter a valid URL.",
  }),
})

interface ProcessInputFormProps {
  appendLog: (log: string, type: string) => void;
}

export function ProcessInputForm({ appendLog }: ProcessInputFormProps) {
  const form = useForm<z.infer<typeof FormSchema>>({
    resolver: zodResolver(FormSchema),
    defaultValues: {
      url: "",
    },
  })
 
  const [isLoading, setIsLoading] = useState(false); // State to track loading status
  const [progress, setProgress] = useState(0); // State to track progress

  useEffect(() => {
    if (!isLoading) {
      setProgress(0); // Reset progress when not loading
    }
  }, [isLoading]);

  useEffect(() => {
    if (isLoading) {
      const eventSource = new EventSource(`${process.env.NEXT_PUBLIC_API_URL}/progress_stream/`);  
      eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        setProgress(data.progress);
        console.log("Progress updated:", data.progress);
      };
      return () => {
        eventSource.close();
      };
    }
  }, [isLoading]);

  async function onSubmit(data: z.infer<typeof FormSchema>) {
    setIsLoading(true); // Set loading to true when process starts
    console.log("isLoading set to true");
    setProgress(0); // Reset progress to 0 on new submission
    appendLog(`Processing website: ${data.url}`, "request");

    const requestData = {
      tld: data.url,
    };

    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/process/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestData),
    });

    setIsLoading(false); // Set loading to false when process ends
    console.log("isLoading set to false");

    if (response.ok) {
      const result = await response.json();
      appendLog(`Processing initiated: ${JSON.stringify(result)}`, "response");
      toast({
        title: "Processing initiated",
        description: "The website is being processed.",
      });
    } else {
      toast({
        title: "Error",
        description: "There was an error processing the website.",
      });
    }
  }
 
  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="w-full space-y-6">
        <FormField
          control={form.control}
          name="url"
          render={({ field }) => (
            <FormItem>
              <FormLabel>URL</FormLabel>
              <FormControl>
                <Input placeholder="https://mdschool.tcu.edu" {...field} />
              </FormControl>
              <FormDescription>
                Top level domain of the website to scrape.
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <div className="flex justify-left">
          <div className="inline-flex shrink-0">
            {isLoading ? (
              <Progress value={progress}></Progress>
            ) : (
              <Button type="submit">Submit</Button>
            )}
          </div>
        </div>
      </form>
    </Form>
  )
}

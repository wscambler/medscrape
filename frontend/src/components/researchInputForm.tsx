"use client"
 
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { useState, useEffect } from "react" // Import useState and useEffect for handling SSE
 
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
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
import { Textarea } from "@/components/ui/textarea"
import { toast } from "@/components/ui/use-toast"
 
const FormSchema = z.object({
  url: z.string().url({
    message: "Please enter a valid URL.",
  }),
  questions: z.string(), // Expect a string here
})
 
interface ResearchInputFormProps {
  appendLog: (log: string, type: string) => void;
}

export function ResearchInputForm({ appendLog }: ResearchInputFormProps) {
  const form = useForm<z.infer<typeof FormSchema>>({
    resolver: zodResolver(FormSchema),
    defaultValues: {
      url: "",
      questions: "", // Default to an empty string
    },
  })

  const [isLoading, setIsLoading] = useState(false); // Add loading state
  const [progress, setProgress] = useState(0); // Add progress state for dynamic updates
 
  useEffect(() => {
    if (isLoading) {
      const eventSource = new EventSource(`${process.env.NEXT_PUBLIC_API_URL}/query_progress_stream/`);
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
    setIsLoading(true); // Start loading
    console.log("isLoading set to true");
    setProgress(0); // Reset progress on new submission
    const processedData = {
      tld: data.url,
      questions: data.questions.split(';').map(question => question.trim()).filter(question => question !== ''),
    };

    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/query/`, {
      method: "POST", 
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(processedData),
    });

    if (response.ok) {
      const result = await response.json();
      appendLog(`Query submitted: ${JSON.stringify(result)}`, "response");
      toast({
        title: "Query submitted",
        description: "The query has been submitted for processing.",
      });
    } else {
      toast({
        title: "Error",
        description: "There was an error submitting the query.",
      });
      setIsLoading(false); // Stop loading on error
      console.log("isLoading set to false");
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
                Website to filter the search.
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="questions"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Questions</FormLabel>
              <FormControl>
                <Textarea placeholder="What are the core values?; What is the curriculum?" {...field} />
              </FormControl>
              <FormDescription>
                List your questions separated by a semicolon (;)
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

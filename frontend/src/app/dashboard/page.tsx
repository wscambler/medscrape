"use client"

import { Dashboard } from "@/components/Dashboard";
// use client
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const navigation = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const isAuthenticated = localStorage.getItem("isLoggedIn");
    setIsAuthenticated(!!isAuthenticated);
    if (!isAuthenticated) {
      navigation.push('/login');
    }
  }, [navigation]);

  return (
    <main className="flex min-h-screen flex-col items-center overflow-hidden justify-between">
      <Dashboard isAuthenticated={isAuthenticated} />
    </main>
  );
}
"use client";

import { toast } from "sonner";
import { useEffect } from "react";
import { CheckCircle, Flame } from "lucide-react";
import { useAuth } from "@/lib/auth/context"
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useRouter, useSearchParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const standardPlans = [
  {
    id: "free",
    name: "Free",
    price: "€0",
    description: "Basic alerts with limited preferences",
    features: ["Limited filters", "1 active search", "Community support"],
    priceId: process.env.NEXT_PUBLIC_STRIPE_PRICE_FREE,
  },
  {
    id: "proMon",
    name: "Monthly Subscription",
    price: "€9/mo",
    description: "Unlock advanced filters and multiple searches",
    features: ["Unlimited filters", "Up to 10 active searches", "Priority email support"],
    priceId: process.env.NEXT_PUBLIC_STRIPE_PRICE_MO,
  },
  {
    id: "pro3Mon",
    name: "3 Month Subscription",
    price: "€24 (3mo)",
    description: "Same benefits as Monthly, with a discount",
    features: [],
    priceId: process.env.NEXT_PUBLIC_STRIPE_PRICE_3MO,
    popular: true,
    savings: "€8/mo equivalent",
    saveLabel: "Save 11%"
  },
];

const lifetimePlan = {
  id: "lifetime",
  name: "Lifetime",
  price: "€199",
  description: "One-time payment for lifetime access",
  features: ["Unlimited everything", "Lifetime updates", "VIP support"],
  priceId: process.env.NEXT_PUBLIC_STRIPE_PRICE_LIFETIME,
};

export default function SubscriptionPage() {
  const { user, organization } = useAuth()

  // Handle Poster Notifications if status is set
  const searchParams = useSearchParams();
  useEffect(() => {
    const status = searchParams.get("status");
    setTimeout(() => {
      if (status === "success") {
        toast.success("🎉 Subscription updated. Thanks for upgrading your plan!");
      } else if (status === "cancel") {
        toast("Checkout canceled. No changes were made to your plan.");
      } else if (status === "error") {
        toast.error("Something went wrong. Please try again later.");
      }
    }, 500); // Delay just enough to wait for hydration otherwise, toaster wasn't showing
  }, [searchParams]); 
  
  
  const handleCheckout = async (priceId: string) => {
    const res = await fetch("/api/create-checkout-session", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ priceId, email: user.email ?? "mock@example.com" }),
    });
  
    if (!res.ok) {
      const error = await res.text();
      console.error("Checkout error:", error);
      toast.error("Something went wrong starting checkout.");
      return;
    }
  
    const { url } = await res.json();
    window.location.href = url;
  };  

  return (
    <div className="max-w-5xl mx-auto px-4 py-10 space-y-8">
      <h1 className="text-3xl font-bold">Your Plan</h1>

      <div className="grid gap-6 md:grid-cols-3">
        {standardPlans.map((plan) => {
          const isCurrent = organization.subscriptionId === plan.id;
          return (
            <Card
              key={plan.name}
              className={`relative flex flex-col justify-between h-full ${
                isCurrent ? "border-2 border-primary bg-muted/10" : "border border-muted"
              }`}
            >
              <CardHeader className="pb-2">
                <CardTitle className="flex items-start justify-between">
                  <div className="flex flex-col">
                    <span>{plan.name}</span>
                    {plan.savings && (
                      <span className="text-xs text-green-500 mt-1">{plan.saveLabel}</span>
                    )}
                  </div>
                  <div className="flex gap-1">
                    {plan.popular && (
                      <Badge className="bg-orange-500 text-white">Popular</Badge>
                    )}
                    {isCurrent && <Badge variant="outline">Current Plan</Badge>}
                  </div>
                </CardTitle>
                <p className="text-muted-foreground text-sm mt-2">{plan.description}</p>
              </CardHeader>
              <CardContent className="space-y-4 flex flex-col flex-1 justify-between">
                <div>
                  <p className="text-2xl font-semibold">{plan.price}</p>
                  <ul className="text-sm text-muted-foreground space-y-1 mt-2">
                    {plan.features.map((feature) => (
                      <li key={feature} className="flex items-center">
                        <CheckCircle className="h-4 w-4 mr-2 text-primary" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                </div>
                {isCurrent ? (
                  <Button className="w-full mt-4" disabled>
                    Selected ✓
                  </Button>
                ) : (
                  <Button className="w-full mt-4" onClick={() => handleCheckout(plan.priceId)}>
                    Upgrade
                  </Button>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="rounded-lg border bg-muted/20 p-4 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm sm:text-base">
          <Flame className="h-5 w-5 text-yellow-500" />
          <span className="font-medium text-foreground">
            Lifetime Deal — One-time payment of <span className="font-semibold">{lifetimePlan.price}</span>
          </span>
        </div>
        <Button className="text-sm whitespace-nowrap" onClick={() => handleCheckout(lifetimePlan.priceId)}>
          Upgrade to Lifetime
        </Button>
      </div>
    </div>
  );
}

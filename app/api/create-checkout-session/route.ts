import Stripe from "stripe";
import { NextRequest, NextResponse } from "next/server";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: "2023-10-16",
});

export async function POST(req: NextRequest) {
  const { priceId, email } = await req.json();

  try {
    const session = await stripe.checkout.sessions.create({
      payment_method_types: ["card", "ideal"], // PayPal coming soon to Checkout
      mode: "subscription",
      customer_email: email,
      line_items: [{ price: priceId, quantity: 1 }],
      success_url: process.env.NEXT_PUBLIC_STRIPE_SUCCESS_URL!,
      cancel_url: process.env.NEXT_PUBLIC_STRIPE_CANCEL_URL!,
    });

    return NextResponse.json({ url: session.url });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

import os
import stripe
from flask import Flask, request, jsonify

app = Flask(__name__)

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
MAX_PAYMENTS = int(os.environ.get("MAX_PAYMENTS", "3"))

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except stripe.error.SignatureVerificationError:
        return jsonify({"error": "Invalid signature"}), 400

    if event["type"] == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        subscription_id = invoice.get("subscription")

        if not subscription_id:
            return jsonify({"status": "no subscription"}), 200

        # Récupérer tous les paiements réussis pour cet abonnement
        invoices = stripe.Invoice.list(
            subscription=subscription_id,
            status="paid",
        )

        paid_count = len(invoices.data)
        print(f"Abonnement {subscription_id} — paiements réussis : {paid_count}/{MAX_PAYMENTS}")

        if paid_count >= MAX_PAYMENTS:
            # Annuler l'abonnement à la fin de la période en cours
            stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            print(f"✅ Abonnement {subscription_id} annulé après {MAX_PAYMENTS} paiements.")

    return jsonify({"status": "ok"}), 200

@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "Webhook Méthode R.E.S.P.E.C.T actif 🌿"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

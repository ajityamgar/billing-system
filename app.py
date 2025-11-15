from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Dict, Any
from urllib.parse import urlencode
import io
import uuid

from flask import Flask, render_template, request, jsonify, session, send_from_directory


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    # For demo purposes only. In production, load from env var.
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-me")

    # Load sample product database
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    products_path = os.path.join(data_dir, "products.json")
    with open(products_path, "r", encoding="utf-8") as f:
        products: Dict[str, Dict[str, Any]] = json.load(f)

    TAX_RATE = float(os.environ.get("TAX_RATE", "0.18"))  # 18% default
    UPI_VPA = os.environ.get("UPI_VPA", "merchant@upi")
    UPI_NAME = os.environ.get("UPI_NAME", "Supermarket")

    def get_cart() -> Dict[str, Dict[str, Any]]:
        cart = session.get("cart")
        if cart is None:
            cart = {}
            session["cart"] = cart
        return cart

    def save_cart(cart: Dict[str, Dict[str, Any]]) -> None:
        session["cart"] = cart

    def clear_cart() -> None:
        session.pop("cart", None)

    def calculate_totals(cart: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        subtotal = 0.0
        items = []
        for code, entry in cart.items():
            qty = int(entry.get("quantity", 1))
            price = float(entry.get("price", 0))
            line_total = qty * price
            subtotal += line_total
            items.append({
                "code": code,
                "name": entry.get("name"),
                "category": entry.get("category"),
                "price": price,
                "quantity": qty,
                "line_total": round(line_total, 2),
            })
        tax = round(subtotal * TAX_RATE, 2)
        total = round(subtotal + tax, 2)
        return {
            "items": items,
            "subtotal": round(subtotal, 2),
            "tax": tax,
            "tax_rate": TAX_RATE,
            "total": total,
        }

    @app.route("/")
    def index():
        return render_template("index.html")

    # Serve assets from templates folder (no static directory desired)
    @app.get("/style.css")
    def style_css():
        return send_from_directory(app.template_folder, "style.css", mimetype="text/css")

    @app.get("/script.js")
    def script_js():
        return send_from_directory(app.template_folder, "script.js", mimetype="application/javascript")

    @app.post("/add_to_cart")
    def add_to_cart():
        data = request.get_json(silent=True) or request.form
        code = (data.get("code") or "").strip()
        quantity = int(data.get("quantity", 1))
        if not code:
            return jsonify({"ok": False, "error": "Product code is required"}), 400

        product = products.get(code)
        if not product:
            return jsonify({"ok": False, "error": "Product not found"}), 404

        cart = get_cart()
        existing = cart.get(code)
        if existing:
            existing_qty = int(existing.get("quantity", 1))
            existing["quantity"] = max(1, existing_qty + quantity)
        else:
            cart[code] = {
                "name": product["name"],
                "price": float(product["price"]),
                "category": product.get("category", "General"),
                "quantity": max(1, quantity),
            }
        save_cart(cart)
        return jsonify({"ok": True, "cart": calculate_totals(cart)})

    @app.post("/update_item")
    def update_item():
        data = request.get_json(silent=True) or request.form
        code = (data.get("code") or "").strip()
        quantity = int(data.get("quantity", 0))
        cart = get_cart()
        if code not in cart:
            return jsonify({"ok": False, "error": "Item not in cart"}), 404
        if quantity <= 0:
            cart.pop(code, None)
        else:
            cart[code]["quantity"] = quantity
        save_cart(cart)
        return jsonify({"ok": True, "cart": calculate_totals(cart)})

    @app.post("/remove_item")
    def remove_item():
        data = request.get_json(silent=True) or request.form
        code = (data.get("code") or "").strip()
        cart = get_cart()
        if code in cart:
            cart.pop(code)
            save_cart(cart)
            return jsonify({"ok": True, "cart": calculate_totals(cart)})
        return jsonify({"ok": False, "error": "Item not in cart"}), 404

    @app.get("/cart")
    def get_cart_route():
        cart = get_cart()
        return jsonify({"ok": True, "cart": calculate_totals(cart)})

    @app.post("/checkout")
    def checkout():
        cart = get_cart()
        if not cart:
            return jsonify({"ok": False, "error": "Cart is empty"}), 400
        totals = calculate_totals(cart)
        return jsonify({"ok": True, "cart": totals})

    def build_upi_deeplink(amount: float, note: str) -> str:
        params = {
            "pa": UPI_VPA,
            "pn": UPI_NAME,
            "am": f"{amount:.2f}",
            "tn": note,
            "cu": "INR",
        }
        return f"upi://pay?{urlencode(params)}"

    def format_bill_text(totals: Dict[str, Any], payment_method: str, base_url: str | None = None, invoice_id: str | None = None) -> str:
        lines = [
            "Supermarket Invoice",
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "Items:",
        ]
        for item in totals["items"]:
            lines.append(
                f"- {item['name']} x {item['quantity']} @ {item['price']:.2f} = {item['line_total']:.2f}"
            )
        lines.extend([
            "",
            f"Subtotal: {totals['subtotal']:.2f}",
            f"Tax ({int(TAX_RATE*100)}%): {totals['tax']:.2f}",
            f"Total: {totals['total']:.2f}",
            "",
            f"Payment via {payment_method}",
        ])

        if payment_method.lower() == "upi":
            note = "Supermarket Bill"
            deeplink = build_upi_deeplink(totals['total'], note)
            lines.append(f"UPI Link: {deeplink}")
            if base_url:
                amount_str = "{:.2f}".format(totals['total'])
                qr_url = f"{base_url}upi_qr?{urlencode({'am': amount_str, 'tn': note})}"
                lines.append(f"Scan QR: {qr_url}")

        if base_url and invoice_id:
            lines.append("")
            lines.append(f"Invoice PDF: {base_url}invoice_pdf?inv={invoice_id}")

        lines.append(" Thank you for shopping with us! Happy shopping!")
        return "\n".join(lines)

    def send_whatsapp_message(phone: str, message: str, media_url: str | None = None) -> Dict[str, Any]:
        # Prefer pywhatkit for simple simulation; fallback to Twilio if env vars provided
        # If neither available, simulate success.
        try:
            import pywhatkit  # type: ignore

            # pywhatkit requires a short delay time target; use instantly API
            # It opens WhatsApp Web; ensure the environment has a browser.
            pywhatkit.sendwhatmsg_instantly(phone_no=phone, message=message, wait_time=10, tab_close=True)
            return {"ok": True, "provider": "pywhatkit"}
        except Exception as e:  # noqa: BLE001
            # Try Twilio if configured
            account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
            auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
            from_whatsapp = os.environ.get("TWILIO_WHATSAPP_FROM")  # like 'whatsapp:+14155238886'
            if account_sid and auth_token and from_whatsapp:
                try:
                    from twilio.rest import Client  # type: ignore

                    client = Client(account_sid, auth_token)
                    client.messages.create(
                        from_=from_whatsapp,
                        body=message,
                        to=f"whatsapp:{phone}",
                        media_url=[media_url] if media_url else None,
                    )
                    return {"ok": True, "provider": "twilio"}
                except Exception as twilio_err:  # noqa: BLE001
                    return {"ok": False, "error": str(twilio_err), "provider": "twilio"}
            # As a final fallback, simulate sending in logs
            app.logger.warning("WhatsApp send simulated (no provider). Message to %s: %s", phone, message)
            return {"ok": True, "provider": "simulated", "note": str(e)}

    @app.post("/send_bill")
    def send_bill():
        data = request.get_json(silent=True) or request.form
        payment_method = (data.get("payment_method") or "").strip() or "Cash"
        phone = (data.get("phone") or "").strip()
        if not phone:
            return jsonify({"ok": False, "error": "Phone number is required"}), 400

        cart = get_cart()
        if not cart:
            return jsonify({"ok": False, "error": "Cart is empty"}), 400

        totals = calculate_totals(cart)
        base_url = request.url_root
        invoice_id = uuid.uuid4().hex[:10]
        # Persist last invoice totals in session for PDF retrieval
        session["last_invoice"] = {"id": invoice_id, "totals": totals, "created_at": datetime.now().isoformat()}
        message = format_bill_text(totals, payment_method, base_url, invoice_id)
        pdf_url = f"{base_url}invoice_pdf?inv={invoice_id}"
        result = send_whatsapp_message(phone, message, media_url=pdf_url)
        if result.get("ok"):
            # Clear cart after successful send
            clear_cart()
            return jsonify({"ok": True, "message": "Bill sent to WhatsApp", "provider": result.get("provider")})
        return jsonify({"ok": False, "error": result.get("error", "Failed to send message")}), 500

    @app.get("/invoice_pdf")
    def invoice_pdf():
        try:
            inv = (request.args.get("inv") or "").strip()
        except Exception:
            inv = ""

        # Pull last invoice from session. In production, fetch by id from DB.
        last_invoice = session.get("last_invoice") or {}
        if not last_invoice or (inv and last_invoice.get("id") != inv):
            return ("Invoice not found", 404)

        totals = last_invoice.get("totals") or {}

        try:
            from reportlab.pdfgen import canvas  # type: ignore
            from reportlab.lib.pagesizes import A4  # type: ignore
            from reportlab.lib.units import mm  # type: ignore

            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4

            y = height - 30 * mm
            c.setFont("Helvetica-Bold", 16)
            c.drawString(20 * mm, y, "Supermarket Invoice")
            y -= 10 * mm
            c.setFont("Helvetica", 10)
            c.drawString(20 * mm, y, f"Invoice: {last_invoice.get('id','N/A')}    Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            y -= 8 * mm
            c.line(20 * mm, y, width - 20 * mm, y)
            y -= 8 * mm

            c.setFont("Helvetica-Bold", 10)
            c.drawString(20 * mm, y, "Item")
            c.drawString(90 * mm, y, "Qty")
            c.drawString(110 * mm, y, "Price")
            c.drawString(140 * mm, y, "Total")
            y -= 6 * mm
            c.setFont("Helvetica", 10)

            for item in totals.get("items", []):
                if y < 30 * mm:
                    c.showPage()
                    y = height - 30 * mm
                    c.setFont("Helvetica", 10)
                c.drawString(20 * mm, y, item["name"])
                c.drawRightString(105 * mm, y, str(item["quantity"]))
                c.drawRightString(130 * mm, y, f"{item['price']:.2f}")
                c.drawRightString(width - 20 * mm, y, f"{item['line_total']:.2f}")
                y -= 6 * mm

            y -= 6 * mm
            c.line(20 * mm, y, width - 20 * mm, y)
            y -= 8 * mm
            c.setFont("Helvetica-Bold", 11)
            c.drawRightString(130 * mm, y, "Subtotal:")
            c.drawRightString(width - 20 * mm, y, f"{totals['subtotal']:.2f}")
            y -= 6 * mm
            c.setFont("Helvetica", 10)
            c.drawRightString(130 * mm, y, f"Tax ({int(TAX_RATE*100)}%):")
            c.drawRightString(width - 20 * mm, y, f"{totals['tax']:.2f}")
            y -= 6 * mm
            c.setFont("Helvetica-Bold", 12)
            c.drawRightString(130 * mm, y, "Total:")
            c.drawRightString(width - 20 * mm, y, f"{totals['total']:.2f}")

            y -= 12 * mm
            c.setFont("Helvetica", 9)
            c.drawString(20 * mm, y, " Thank you for shopping with us! Happy shopping! ")

            c.showPage()
            c.save()
            pdf = buffer.getvalue()
            buffer.close()
            return app.response_class(pdf, mimetype="application/pdf")
        except Exception as e:  # noqa: BLE001
            app.logger.exception("Failed generating PDF: %s", e)
            return ("Failed to generate PDF", 500)

    @app.get("/upi_qr")
    def upi_qr():
        try:
            amount_str = request.args.get("am") or request.args.get("amount") or "0.00"
            amount = float(amount_str)
            note = request.args.get("tn") or request.args.get("note") or "Supermarket Bill"
        except Exception:
            return ("Invalid parameters", 400)

        deeplink = build_upi_deeplink(amount, note)
        try:
            import qrcode  # type: ignore
            img = qrcode.make(deeplink)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            return app.response_class(buf.getvalue(), mimetype="image/png")
        except Exception as e:  # noqa: BLE001
            app.logger.exception("Failed generating UPI QR: %s", e)
            return ("Failed to generate QR", 500)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)



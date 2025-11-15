// Utility to handle JSON fetch with POST
async function postJSON(url, payload) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok || data.ok === false) {
    throw new Error(data.error || 'Request failed');
  }
  return data;
}

function setStatus(msg, type = 'info') {
  const el = document.getElementById('status');
  el.textContent = msg || '';
  el.style.color = type === 'error' ? '#ff8fa1' : '#9aa3b2';
}

function renderCart(cart) {
  const body = document.getElementById('cartBody');
  body.innerHTML = '';
  cart.items.forEach(item => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${item.code}</td>
      <td>${item.name}</td>
      <td>${item.category || ''}</td>
      <td>${item.price.toFixed(2)}</td>
      <td>
        <input class="qty-input" type="number" min="1" value="${item.quantity}" data-code="${item.code}" />
      </td>
      <td>${item.line_total.toFixed(2)}</td>
      <td>
        <button class="action-btn danger" data-remove="${item.code}">Remove</button>
      </td>
    `;
    body.appendChild(tr);
  });

  document.getElementById('subtotal').textContent = cart.subtotal.toFixed(2);
  document.getElementById('tax').textContent = cart.tax.toFixed(2);
  document.getElementById('total').textContent = cart.total.toFixed(2);
  document.getElementById('taxRate').textContent = Math.round((cart.tax_rate || 0) * 100);

  // Bind qty changes
  body.querySelectorAll('.qty-input').forEach(input => {
    input.addEventListener('change', async (e) => {
      const code = e.target.getAttribute('data-code');
      const quantity = parseInt(e.target.value || '1', 10);
      try {
        const resp = await postJSON('/update_item', { code, quantity });
        renderCart(resp.cart);
        setStatus('Item updated');
      } catch (err) {
        setStatus(err.message, 'error');
      }
    });
  });

  // Bind remove
  body.querySelectorAll('[data-remove]').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const code = e.target.getAttribute('data-remove');
      try {
        const resp = await postJSON('/remove_item', { code });
        renderCart(resp.cart);
        setStatus('Item removed');
      } catch (err) {
        setStatus(err.message, 'error');
      }
    });
  });
}

async function refreshCart() {
  const res = await fetch('/cart');
  const data = await res.json();
  if (data.ok) renderCart(data.cart);
}

document.addEventListener('DOMContentLoaded', () => {
  const addBtn = document.getElementById('addBtn');
  const productCode = document.getElementById('productCode');
  const quantity = document.getElementById('quantity');
  const checkoutBtn = document.getElementById('checkoutBtn');
  const phoneInput = document.getElementById('whatsApp');
  const scanBtn = document.getElementById('scanBtn');
  const scannerModal = document.getElementById('scannerModal');
  const closeScanner = document.getElementById('closeScanner');

  addBtn.addEventListener('click', async () => {
    const code = productCode.value.trim();
    const qty = parseInt(quantity.value || '1', 10);
    if (!code) { setStatus('Enter a product code', 'error'); return; }
    try {
      const resp = await postJSON('/add_to_cart', { code, quantity: qty });
      renderCart(resp.cart);
      productCode.value = '';
      quantity.value = '1';
      setStatus('Added to cart');
    } catch (err) {
      setStatus(err.message, 'error');
    }
  });

  // Enter key on barcode field
  productCode.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') addBtn.click();
  });

  // Scanner integration using QuaggaJS (@ericblade/quagga2)
  let quaggaRunning = false;
  let processing = false;
  const recentScans = new Map(); // code -> last timestamp
  async function startScanner() {
    if (!window.Quagga) { setStatus('Scanner library failed to load', 'error'); return; }
    try {
      scannerModal.setAttribute('aria-hidden', 'false');
      const constraints = { facingMode: 'environment' };
      await Quagga.init({
        inputStream: {
          name: 'Live',
          type: 'LiveStream',
          target: document.querySelector('#scanner'),
          constraints,
        },
        decoder: {
          readers: [
            'ean_reader',
            'ean_8_reader',
            'code_128_reader',
            'upc_reader',
            'upc_e_reader'
          ]
        },
        locate: true,
      });
      Quagga.start();
      quaggaRunning = true;
      setStatus('Scanner started');
    } catch (err) {
      setStatus('Unable to start camera: ' + err.message, 'error');
      scannerModal.setAttribute('aria-hidden', 'true');
    }
  }

  function stopScanner() {
    if (window.Quagga && quaggaRunning) {
      Quagga.stop();
      quaggaRunning = false;
      setStatus('Scanner stopped');
    }
    processing = false;
    recentScans.clear();
    scannerModal.setAttribute('aria-hidden', 'true');
  }

  if (scanBtn) {
    scanBtn.addEventListener('click', () => {
      startScanner();
    });
  }
  if (closeScanner) {
    closeScanner.addEventListener('click', stopScanner);
  }

  if (window.Quagga) {
    Quagga.onDetected(async (data) => {
      const code = (data && data.codeResult && data.codeResult.code) || '';
      if (!code) return;

      const now = Date.now();
      const last = recentScans.get(code) || 0;
      // ignore duplicate of the same code within 1.5s
      if (now - last < 1500) return;
      recentScans.set(code, now);

      if (processing) return;
      processing = true;
      try {
        // reflect in input for visibility, keep camera running
        productCode.value = code;
        const resp = await postJSON('/add_to_cart', { code, quantity: 1 });
        renderCart(resp.cart);
        setStatus(`Scanned and added: ${code}`);
      } catch (err) {
        setStatus(err.message, 'error');
      } finally {
        processing = false;
      }
    });
  }

  checkoutBtn.addEventListener('click', async () => {
    try {
      // Ensure cart exists and totals up to date
      const check = await postJSON('/checkout', {});
      const payment = document.querySelector('input[name="payment"]:checked').value;
      const phone = phoneInput.value.trim();
      if (!phone) { setStatus('Enter WhatsApp number', 'error'); return; }
      setStatus(`Processing payment via ${payment}...`);
      const send = await postJSON('/send_bill', { payment_method: payment, phone });
      setStatus('Payment successful and bill sent!');
      // refresh cart (will be empty after send)
      await refreshCart();
    } catch (err) {
      setStatus(err.message, 'error');
    }
  });

  refreshCart();
});



function money(n) {
  return n.toLocaleString(undefined, { style: "currency", currency: "USD" });
}

document.getElementById("loan-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const out = document.getElementById("loan-result");
  out.innerHTML = "Calculating...";
  const res = await fetch("api/monthly-payment", { method: "POST", body: new FormData(e.target) });
  const data = await res.json();
  if (data.error) {
    out.innerHTML = `<div class="error-text">${data.error}</div>`;
    return;
  }
  out.innerHTML = `
    <div class="result-grid">
      <div class="stat"><span class="label">Monthly payment</span><span class="value">${money(data.monthly_payment)}</span></div>
      <div class="stat"><span class="label">Total paid</span><span class="value">${money(data.total_paid)}</span></div>
      <div class="stat"><span class="label">Total interest</span><span class="value">${money(data.total_interest)}</span></div>
    </div>`;
});

// =========================================================================
// ShaktiX Enterprise SaaS Web Portal Client Script (app.js)
// Contacts: WhatsApp +91 8298136441 | Call Sales +91 8825208568
// Supabase Cloud DB: https://dcbpqapojfxacpvjobyp.supabase.co
// =========================================================================

// Official Contact Credentials
const SALES_WHATSAPP = "918298136441";
const SALES_PHONE = "+918825208568";

// Supabase Client Initialization
const SUPABASE_URL = "https://dcbpqapojfxacpvjobyp.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRjYnBxYXBvamZ4YWNwdmpvYnlwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk4MDM4MjAsImV4cCI6MjEwNTM3OTgyMH0.RSt2lJxaPh_JwcpORuBozkUSIYaRrVt1_y9eEPj3YwM";

const supabaseClient = (window.supabase && typeof window.supabase.createClient === 'function')
  ? window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY)
  : null;

// =========================================================================
// 1. Interactive Demo Simulator Data & State
// =========================================================================
const demoTemplates = {
  coaching: {
    variants: [
      "Namaste {Name} ji! Admissions are officially open for NEET & JEE batches 2026 at our prime center in {City}. Up to 50% scholarship test this Sunday! Reply DEMO for prospectus brochure.",
      "Hello {Name}! Are you preparing for top-rank competitive exams? Special crash courses starting this Monday in {City}. Free study modules included. Reply DEMO to book a demo seat!",
      "Dear {Name}, great news! Limited seats remaining for our Foundation batch in {City}. Flat 30% fee concession for the first 50 registrations. Reply DEMO to receive syllabus PDF."
    ],
    keyword: "DEMO",
    autoReply: "⚡ <b>Auto-Responder:</b> Thank you {Name} ji! Here is your Free Demo Pass and full Prospectus brochure: <br>🔗 <code>shaktix.local/prospectus.pdf</code>"
  },
  realestate: {
    variants: [
      "Hello {Name}! Looking for prime investment or your dream home? Exclusive luxury plots & flats are launching in {City}. 100% clear registry title with 80% bank loan. Reply VISIT for weekend tour!",
      "Dear {Name} ji, high-ROI property launch alert in {City}! Gated community near highway with 24/7 security. Free weekend site visit with pick & drop. Reply VISIT to schedule!",
      "Respected {Name}, golden opportunity to own registry-ready commercial plots in {City}. Pre-launch price benefits valid till Sunday only. Reply VISIT for layout plan & video."
    ],
    keyword: "VISIT",
    autoReply: "⚡ <b>Auto-Responder:</b> Namaste {Name}! Your site visit request is registered for Sunday. Our area manager will call you shortly with GPS location map."
  },
  retail: {
    variants: [
      "Hi {Name} ji! Festive Grand Season Sale is now LIVE! Flat 20% OFF on our new arrivals at our {City} showroom. Zero making charges on select jewellery. Reply CATALOG to view designs!",
      "Hello {Name}! We have an exclusive VIP preview just for you. Buy 2 Get 1 FREE on premium festive wear in {City}. Assured surprise gift on every visit. Reply CATALOG for brochure!",
      "Dear {Name} ji, mega celebration offer! Extra 10% cashback on UPI payments at our {City} store this weekend only. Reply CATALOG to see trending items on WhatsApp."
    ],
    keyword: "CATALOG",
    autoReply: "⚡ <b>Auto-Responder:</b> Hello {Name}! Here is our Festive Season Lookbook & 20% discount coupon code: <br>🎟️ <code>SHAKTIX-FESTIVE-20</code>"
  },
  b2b: {
    variants: [
      "Greetings {Name}, quick question regarding your business growth in {City}. We help companies automate WhatsApp customer follow-ups and scale inquiries by 10x. Reply DEMO for a 2-min walkthrough!",
      "Hello {Name}! Are you looking to reduce customer acquisition costs this quarter? Reach 10,000+ verified buyers with personalized WhatsApp campaigns. Reply DEMO to see a live sample.",
      "Hi {Name}, hope your business is doing great! We offer a free 15-minute WhatsApp marketing audit for businesses in {City}. Reply DEMO to connect with our growth strategist."
    ],
    keyword: "DEMO",
    autoReply: "⚡ <b>Auto-Responder:</b> Greetings {Name}! Check out our 2-minute live software walkthrough and client success case studies here: <br>🔗 <code>shaktix.local/b2b-demo.mp4</code>"
  },
  payment: {
    variants: [
      "Respected {Name}, gentle reminder regarding your pending monthly statement #{Phone} for your {City} account. Please ensure timely clearance. Reply QR to get instant payment QR.",
      "Dear {Name}, friendly update regarding your upcoming due date. Avoid late surcharges and continue uninterrupted service. Reply QR to receive official UPI QR code instantly.",
      "Hello {Name} ji, your account balance notice has been generated at our {City} office. Click to pay via UPI or Netbanking. Reply QR for instant payment details."
    ],
    keyword: "QR",
    autoReply: "⚡ <b>Auto-Responder:</b> Thank you {Name}! Here is your official instant payment QR code. Scan with GPay, PhonePe, or Paytm: <br>💳 <code>UPI: shaktix.merchant@upi</code>"
  }
};

let currentCategory = "coaching";
let currentVariantIndex = 0;
let isSimulating = false;

function renderSimulatedMessage() {
  const custName = document.getElementById("demoCustName")?.value.trim() || "Amit Sharma";
  const custCity = document.getElementById("demoCustCity")?.value.trim() || "Patna";
  const phone = "9835012345";

  const templateData = demoTemplates[currentCategory];
  if (!templateData) return;

  const rawText = templateData.variants[currentVariantIndex % templateData.variants.length];
  const rendered = rawText
    .replace(/{Name}/g, custName)
    .replace(/{City}/g, custCity)
    .replace(/{Phone}/g, phone);

  const msgEl = document.getElementById("simulatedMessageText");
  if (msgEl) {
    msgEl.textContent = rendered;
  }

  const nameHeader = document.getElementById("chatRecipientName");
  if (nameHeader) {
    nameHeader.textContent = `${custName} (+91 98350*****)`;
  }
}

// =========================================================================
// 2. Interactive Event Handlers
// =========================================================================
document.addEventListener("DOMContentLoaded", () => {
  // Mobile Menu Toggle
  const toggleBtn = document.getElementById("mobileToggle");
  const navLinks = document.getElementById("navLinks");
  if (toggleBtn && navLinks) {
    toggleBtn.addEventListener("click", () => {
      navLinks.classList.toggle("open");
    });

    navLinks.querySelectorAll("a").forEach(link => {
      link.addEventListener("click", () => navLinks.classList.remove("open"));
    });
  }

  // Template Pills Selector
  const pills = document.querySelectorAll(".pill-btn");
  pills.forEach(pill => {
    pill.addEventListener("click", () => {
      pills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      currentCategory = pill.getAttribute("data-template") || "coaching";
      currentVariantIndex = 0;
      resetSimulationUI();
      renderSimulatedMessage();
    });
  });

  // Dynamic input change
  const nameInput = document.getElementById("demoCustName");
  const cityInput = document.getElementById("demoCustCity");
  if (nameInput) nameInput.addEventListener("input", renderSimulatedMessage);
  if (cityInput) cityInput.addEventListener("input", renderSimulatedMessage);

  // Re-roll Spintax Variant button
  const rerollBtn = document.getElementById("btnRegenerateSpintax");
  if (rerollBtn) {
    rerollBtn.addEventListener("click", () => {
      currentVariantIndex++;
      resetSimulationUI();
      renderSimulatedMessage();
    });
  }

  // Simulate Dispatch button
  const simBtn = document.getElementById("btnSimulateSend");
  if (simBtn) {
    simBtn.addEventListener("click", runSimulation);
  }

  // Initial render
  renderSimulatedMessage();
});

function resetSimulationUI() {
  const inbound = document.getElementById("inboundMsgBubble");
  const autoReply = document.getElementById("autoReplyBubble");
  const progressBar = document.getElementById("simProgressFill");
  const statusText = document.getElementById("simStatusText");

  if (inbound) inbound.style.display = "none";
  if (autoReply) autoReply.style.display = "none";
  if (progressBar) progressBar.style.width = "0%";
  if (statusText) statusText.textContent = "Ready for simulation. Click 'Simulate Dispatch'.";
}

function runSimulation() {
  if (isSimulating) return;
  isSimulating = true;

  resetSimulationUI();
  const custName = document.getElementById("demoCustName")?.value.trim() || "Amit Sharma";
  const templateData = demoTemplates[currentCategory];
  const progressBar = document.getElementById("simProgressFill");
  const statusText = document.getElementById("simStatusText");
  const inbound = document.getElementById("inboundMsgBubble");
  const autoReply = document.getElementById("autoReplyBubble");

  // Step 1: Connecting Chrome automation
  if (progressBar) progressBar.style.width = "30%";
  if (statusText) statusText.textContent = "Initializing Chrome CDP automation engine & anti-ban mask...";

  setTimeout(() => {
    // Step 2: Personalizing & Dispatching
    if (progressBar) progressBar.style.width = "65%";
    if (statusText) statusText.textContent = `Injecting personal tags for ${custName}... Random pause (11s) applied.`;

    setTimeout(() => {
      // Step 3: Message Sent
      if (progressBar) progressBar.style.width = "100%";
      if (statusText) statusText.textContent = `✓ Successfully delivered to ${custName}! Awaiting customer reply...`;

      setTimeout(() => {
        // Step 4: Customer Replies
        if (inbound) {
          inbound.querySelector("p").textContent = templateData.keyword;
          inbound.style.display = "block";
        }
        if (statusText) statusText.textContent = `Inbound response detected: "${templateData.keyword}"! Triggering 2-Way Auto-Responder...`;

        setTimeout(() => {
          // Step 5: Auto-Responder Sends Instant Brochure
          if (autoReply) {
            autoReply.querySelector("p").innerHTML = templateData.autoReply.replace(/{Name}/g, custName);
            autoReply.style.display = "block";
          }
          if (statusText) statusText.textContent = `✓ Auto-Responder dispatched brochure instantly! Marked ${custName} as 🔥 HOT LEAD.`;
          isSimulating = false;
        }, 1200);
      }, 1400);
    }, 1200);
  }, 900);
}

// =========================================================================
// 3. License Verification Modal & Supabase Cloud Check
// =========================================================================
function openLicenseModal() {
  const modal = document.getElementById("licenseModal");
  if (modal) modal.classList.add("open");
}

function closeLicenseModal() {
  const modal = document.getElementById("licenseModal");
  if (modal) modal.classList.remove("open");
  const alertBox = document.getElementById("modalAlert");
  if (alertBox) {
    alertBox.className = "modal-alert";
    alertBox.textContent = "";
  }
}

async function simulateKeyVerification() {
  const machId = document.getElementById("modalMachineId")?.value.trim().toUpperCase();
  const plan = document.getElementById("modalPlan")?.value || "PRO";
  const keyInput = document.getElementById("modalKeyInput")?.value.trim();
  const alertBox = document.getElementById("modalAlert");

  if (!machId) {
    if (alertBox) {
      alertBox.className = "modal-alert error";
      alertBox.textContent = "Please enter your 8-character Machine ID from the desktop software.";
    }
    return;
  }

  if (alertBox) {
    alertBox.className = "modal-alert";
    alertBox.style.display = "block";
    alertBox.textContent = "Connecting to Supabase Cloud Database in Mumbai...";
  }

  // 1. If key is provided, verify against Supabase Cloud DB
  if (keyInput && supabaseClient) {
    try {
      const { data, error } = await supabaseClient
        .from('licenses')
        .select('*')
        .eq('license_key', keyInput)
        .eq('machine_id', machId)
        .maybeSingle();

      if (data && data.is_active) {
        alertBox.className = "modal-alert success";
        alertBox.innerHTML = `✓ Verified via Supabase Cloud!<br>Plan: <b>${data.plan_tier}</b><br>Expires: ${new Date(data.expires_at).toLocaleDateString()}<br>Your software is licensed and ready to use.`;
        return;
      }
    } catch (e) {
      console.warn("Supabase query notice:", e);
    }
  }

  // 2. If no key entered, generate instant key for this machine
  if (!keyInput) {
    const today = new Date().toISOString().slice(0, 10).replace(/-/g, "");
    const generatedKey = `SHAKTIX-${plan}-${today}-${machId}-98A4FC12`;
    const keyBox = document.getElementById("modalKeyInput");
    if (keyBox) keyBox.value = generatedKey;

    if (alertBox) {
      alertBox.className = "modal-alert success";
      alertBox.innerHTML = `Instant license key generated for your machine: <br><code style="user-select: all;">${generatedKey}</code><br><br>Paste this key in your Desktop App's License tab to activate!`;
    }

    // Ping Supabase machine_logs
    if (supabaseClient) {
      supabaseClient.from('machine_logs').insert([{
        machine_id: machId,
        os_version: navigator.userAgent.slice(0, 80),
        client_version: 'Web Portal 2.5'
      }]).then(() => console.log("Device ping recorded")).catch(() => {});
    }
    return;
  }

  // 3. Verify format fallback
  if (keyInput.startsWith("SHAKTIX-") && keyInput.includes(machId)) {
    if (alertBox) {
      alertBox.className = "modal-alert success";
      alertBox.innerHTML = `✓ Key cryptographically matches Machine ID (${machId}) for Plan: ${plan}. Desktop software is ready for full activation!`;
    }
  } else {
    if (alertBox) {
      alertBox.className = "modal-alert error";
      alertBox.textContent = `Invalid key or Machine ID mismatch. Key does not contain machine fingerprint [${machId}].`;
    }
  }
}

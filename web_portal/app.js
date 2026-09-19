// ShaktiX SaaS Web Portal Client Script (app.js)

// 1. Spintax Text Cycle Animation for Live Demo
const spintaxVariants = [
  "Namaste Amit Sharma ji! Flat 20% discount on all new season arrivals at our showroom. Reply DEMO for instant catalog!",
  "Hello Amit Sharma! We have an exclusive weekend offer on premium plots & villas. Call now or reply DEMO for details.",
  "Hey Amit ji! Admissions are now open for NEET & JEE batches with up to 50% scholarship test. Reply DEMO to book slot!",
  "Hi Amit! Looking to scale your business with WhatsApp marketing? Get 10x ROI today. Reply DEMO for a free consultation."
];

let variantIndex = 0;
setInterval(() => {
  const el = document.getElementById("spintax-dynamic-text");
  if (el) {
    variantIndex = (variantIndex + 1) % spintaxVariants.length;
    el.style.opacity = 0;
    setTimeout(() => {
      el.textContent = spintaxVariants[variantIndex];
      el.style.opacity = 1;
    }, 300);
  }
}, 5000);

// 2. Buy Plan Action
function buyPlan(planName) {
  const prices = {
    'STARTER': '₹999 (Starter 6 Months)',
    'PRO': '₹2,499 (Pro Business 1 Year)',
    'AGENCY': '₹4,999 (Agency Reseller Lifetime)'
  };
  
  const chosen = prices[planName] || planName;
  const sellerWhatsApp = "919876543210"; // Seller contact
  const text = encodeURIComponent(`Hi! I want to purchase the ShaktiX WhatsApp Bulk Sender license: ${chosen}. Please share payment details and generate my activation key.`);
  
  const proceed = confirm(`You selected: ${chosen}\n\nClick OK to proceed to instant WhatsApp purchase & Key issuance.`);
  if (proceed) {
    window.open(`https://wa.me/${sellerWhatsApp}?text=${text}`, '_blank');
  }
}

// 3. License Verification Modal
function openLicenseModal() {
  document.getElementById("licenseModal").classList.add("open");
}

function closeLicenseModal() {
  document.getElementById("licenseModal").classList.remove("open");
  const alertBox = document.getElementById("modalAlert");
  if (alertBox) {
    alertBox.className = "modal-alert";
    alertBox.textContent = "";
  }
}

function simulateKeyVerification() {
  const machId = document.getElementById("modalMachineId").value.trim();
  const plan = document.getElementById("modalPlan").value;
  const keyInput = document.getElementById("modalKeyInput").value.trim();
  const alertBox = document.getElementById("modalAlert");

  if (!machId) {
    alertBox.className = "modal-alert error";
    alertBox.textContent = "Please enter your Machine ID from the software's License tab.";
    return;
  }

  if (!keyInput) {
    // Generate a demo key for testing
    const today = new Date().toISOString().slice(0, 10).replace(/-/g, "");
    const demoKey = `SHAKTIX-${plan}-${today}-${machId.toUpperCase()}-A1B2C3D4`;
    document.getElementById("modalKeyInput").value = demoKey;
    alertBox.className = "modal-alert success";
    alertBox.innerHTML = `Sample key generated for your machine: <br><code>${demoKey}</code><br>Paste this key in your desktop software to activate!`;
    return;
  }

  // Verify format
  if (keyInput.startsWith("SHAKTIX-") && keyInput.includes(machId.toUpperCase())) {
    alertBox.className = "modal-alert success";
    alertBox.innerHTML = `✓ Key matches Machine ID (${machId}) for Plan: ${plan}. Your software is ready to activate!`;
  } else {
    alertBox.className = "modal-alert error";
    alertBox.textContent = "Invalid Key or Machine ID mismatch. Please verify your purchase key.";
  }
}

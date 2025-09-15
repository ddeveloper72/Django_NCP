/**
 * Patient Session Cleanup JavaScript
 * Handles automatic cleanup of patient session data when browser closes
 */

class PatientSessionCleanup {
  constructor() {
    this.isCleanupEnabled = true;
    this.cleanupEndpoint = "/api/clear-patient-session/";
    this.emergencyEndpoint = "/api/emergency-session-cleanup/";
    this.init();
  }

  init() {
    // Handle browser/tab close events
    window.addEventListener("beforeunload", (event) => {
      if (this.isCleanupEnabled) {
        this.performCleanup();
      }
    });

    // Handle page visibility changes (tab switching, browser minimizing)
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "hidden" && this.isCleanupEnabled) {
        // Delay cleanup slightly to avoid interfering with normal navigation
        setTimeout(() => {
          if (document.visibilityState === "hidden") {
            this.performCleanup();
          }
        }, 2000);
      }
    });

    // Handle page unload (navigation away)
    window.addEventListener("unload", () => {
      if (this.isCleanupEnabled) {
        this.performCleanup();
      }
    });

    // Add manual cleanup button functionality if present
    this.attachManualCleanupButtons();
  }

  performCleanup() {
    try {
      // Use sendBeacon for reliability during page unload
      if (navigator.sendBeacon) {
        const formData = new FormData();
        formData.append("cleanup_reason", "browser_close");
        navigator.sendBeacon(this.cleanupEndpoint, formData);
        console.log("Patient session cleanup triggered (sendBeacon)");
      } else {
        // Fallback to synchronous request
        this.synchronousCleanup();
      }
    } catch (error) {
      console.error("Failed to perform patient session cleanup:", error);
    }
  }

  synchronousCleanup() {
    try {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", this.cleanupEndpoint, false); // Synchronous
      xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
      xhr.send("cleanup_reason=browser_close");
      console.log("Patient session cleanup triggered (synchronous)");
    } catch (error) {
      console.error("Synchronous cleanup failed:", error);
    }
  }

  manualCleanup() {
    return fetch(this.cleanupEndpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
      body: JSON.stringify({
        cleanup_reason: "manual",
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          console.log(
            "Manual patient session cleanup successful:",
            data.message
          );
          this.showNotification("Patient data cleared successfully", "success");
          return data;
        } else {
          throw new Error(data.error || "Unknown error");
        }
      })
      .catch((error) => {
        console.error("Manual cleanup failed:", error);
        this.showNotification(
          "Failed to clear patient data: " + error.message,
          "error"
        );
        throw error;
      });
  }

  emergencyCleanup() {
    return fetch(this.emergencyEndpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
      body: JSON.stringify({
        cleanup_reason: "emergency",
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          console.log("Emergency session cleanup successful:", data.message);
          this.showNotification(
            "All session data cleared (emergency cleanup)",
            "warning"
          );
          return data;
        } else {
          throw new Error(data.error || "Unknown error");
        }
      })
      .catch((error) => {
        console.error("Emergency cleanup failed:", error);
        this.showNotification(
          "Emergency cleanup failed: " + error.message,
          "error"
        );
        throw error;
      });
  }

  attachManualCleanupButtons() {
    // Attach to manual cleanup buttons
    const cleanupButtons = document.querySelectorAll(
      '[data-action="clear-patient-session"]'
    );
    cleanupButtons.forEach((button) => {
      button.addEventListener("click", (event) => {
        event.preventDefault();

        if (
          confirm("Are you sure you want to clear all patient session data?")
        ) {
          button.disabled = true;
          button.textContent = "Clearing...";

          this.manualCleanup().finally(() => {
            button.disabled = false;
            button.textContent = "Clear Patient Data";
          });
        }
      });
    });

    // Attach to emergency cleanup buttons
    const emergencyButtons = document.querySelectorAll(
      '[data-action="emergency-session-cleanup"]'
    );
    emergencyButtons.forEach((button) => {
      button.addEventListener("click", (event) => {
        event.preventDefault();

        if (
          confirm(
            "EMERGENCY CLEANUP: This will clear ALL session data. Are you sure?"
          )
        ) {
          button.disabled = true;
          button.textContent = "Emergency Cleanup...";

          this.emergencyCleanup().finally(() => {
            button.disabled = false;
            button.textContent = "Emergency Cleanup";
          });
        }
      });
    });
  }

  showNotification(message, type = "info") {
    // Try to use Django messages framework if available
    const messagesContainer = document.querySelector(".messages");
    if (messagesContainer) {
      const messageDiv = document.createElement("div");
      messageDiv.className = `alert alert-${type} alert-dismissible fade show`;
      messageDiv.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
      messagesContainer.appendChild(messageDiv);

      // Auto-remove after 5 seconds
      setTimeout(() => {
        messageDiv.remove();
      }, 5000);
    } else {
      // Fallback to console log
      console.log(`${type.toUpperCase()}: ${message}`);
    }
  }

  disable() {
    this.isCleanupEnabled = false;
    console.log("Patient session cleanup disabled");
  }

  enable() {
    this.isCleanupEnabled = true;
    console.log("Patient session cleanup enabled");
  }
}

// Initialize cleanup system when DOM is ready
document.addEventListener("DOMContentLoaded", function () {
  window.patientSessionCleanup = new PatientSessionCleanup();
  console.log("Patient session cleanup system initialized");
});

// Make functions available globally for button onclick handlers
window.clearPatientSession = function () {
  if (window.patientSessionCleanup) {
    return window.patientSessionCleanup.manualCleanup();
  }
};

window.emergencySessionCleanup = function () {
  if (window.patientSessionCleanup) {
    return window.patientSessionCleanup.emergencyCleanup();
  }
};

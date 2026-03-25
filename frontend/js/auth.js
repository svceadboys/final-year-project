/**
 * auth.js
 * Included at the top of every protected HTML page.
 * Checks for JWT token in local storage and redirects to login if missing.
 */

// Define global logout function
window.logout = function () {
    localStorage.removeItem("admin_token");
    localStorage.removeItem("admin_email");
    window.location.href = "login.html";
};

(function () {
    const token = localStorage.getItem("admin_token");
    const isLoginPage = window.location.pathname.endsWith("login.html");

    if (!token && !isLoginPage) {
        // Not authenticated, redirect to login
        window.location.replace("login.html");
        return;
    } else if (token && isLoginPage) {
        // Already authenticated, skip login page
        window.location.replace("index.html");
        return;
    }

    // Once DOM is loaded, apply the user email and build a logout button on main layout
    if (!isLoginPage) {
        window.addEventListener("DOMContentLoaded", () => {
            const email = localStorage.getItem("admin_email") || "Admin User";

            // Insert logout button dynamically in the sidebar footer
            const footer = document.querySelector(".sidebar-footer");
            if (footer) {
                const logoutHtml = `
                    <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border); text-align: center;">
                        <a href="#" onclick="logout(); return false;" style="color: var(--red); font-size: 13px; text-decoration: none; font-weight: 500;">🚪 Sign Out</a>
                    </div>
                `;
                footer.insertAdjacentHTML("beforeend", logoutHtml);
            }

            // Update email UI
            const emailSpan = document.querySelector(".user-info .name");
            if (emailSpan) emailSpan.innerText = email;
            const letter = email.charAt(0).toUpperCase();
            const avatarSpan = document.querySelector(".user-info .user-avatar");
            if (avatarSpan) avatarSpan.innerText = letter;
        });
    }
})();

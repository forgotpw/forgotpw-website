const menuToggle = document.querySelector(".menu-toggle");
const navigation = document.querySelector("#navigation");

if (menuToggle && navigation) {
  menuToggle.hidden = false;
  const closeMenu = () => {
    menuToggle.setAttribute("aria-expanded", "false");
    navigation.classList.remove("is-open");
  };
  menuToggle.addEventListener("click", () => {
    const isOpen = menuToggle.getAttribute("aria-expanded") === "true";
    menuToggle.setAttribute("aria-expanded", String(!isOpen));
    navigation.classList.toggle("is-open", !isOpen);
  });
  navigation.addEventListener("click", (event) => {
    if (event.target.closest("a")) closeMenu();
  });
  document.addEventListener("keydown", (event) => {
    if (
      event.key === "Escape" &&
      menuToggle.getAttribute("aria-expanded") === "true"
    ) {
      closeMenu();
      menuToggle.focus();
    }
  });
}

// A direct link to an FAQ answer should reveal it as well as scroll to it.
function revealLinkedAnswer() {
  const answer = document.getElementById(window.location.hash.slice(1));
  if (answer instanceof HTMLDetailsElement) answer.open = true;
}
window.addEventListener("hashchange", revealLinkedAnswer);
revealLinkedAnswer();

// Preserve the existing SMS conversion event on the redesigned calls to action.
const campaign = new URLSearchParams(window.location.search).get('utm_campaign');
const fromAd = new URLSearchParams(window.location.search).get('utm_medium') === 'paid_social';
const campaignGreeting = campaign === 'rosa_good_dog_oct2026' && fromAd
  ? 'Hi Rosa! I saw your ad.' : null;
// Use the common Apple &body convention; other clients use standard ?body.
// A real phone composer check is required before a campaign uses this handoff.
const appleMessages = /iPhone|iPad|iPod/.test(navigator.userAgent) ||
  (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
document.querySelectorAll('a[href^="sms:"]').forEach((link) => {
  if (campaignGreeting) {
    link.href = link.getAttribute('href') + (appleMessages ? '&body=' : '?body=') +
      encodeURIComponent(campaignGreeting);
  }
  link.addEventListener("click", () => {
    if (typeof fireConversionScripts === "function") fireConversionScripts();
  });
});

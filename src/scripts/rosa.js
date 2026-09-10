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
document.querySelectorAll('a[href^="sms:"]').forEach((link) => {
  link.addEventListener("click", () => {
    if (typeof fireConversionScripts === "function") fireConversionScripts();
  });
});

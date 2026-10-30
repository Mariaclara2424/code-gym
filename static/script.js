// Tab no campo de código insere 4 espaços (em vez de pular para o próximo campo)
document.querySelectorAll("textarea.codigo").forEach((campo) => {
  const contador = campo.parentElement.querySelector(".contador");

  function atualizarContador() {
    if (!contador) return;
    const linhas = campo.value === "" ? 0 : campo.value.split("\n").length;
    contador.textContent = `${linhas} linha${linhas === 1 ? "" : "s"}`;
  }

  campo.addEventListener("keydown", (evento) => {
    if (evento.key !== "Tab") return;
    evento.preventDefault();
    campo.setRangeText("    ", campo.selectionStart, campo.selectionEnd, "end");
    atualizarContador();
  });

  campo.addEventListener("input", atualizarContador);
});

// Cores no código das soluções (highlight.js, carregado no base.html)
if (window.hljs) hljs.highlightAll();

// Pede confirmação antes de enviar formulários marcados com data-confirmar
document.querySelectorAll("form[data-confirmar]").forEach((form) => {
  form.addEventListener("submit", (evento) => {
    if (!confirm(form.dataset.confirmar)) evento.preventDefault();
  });
});

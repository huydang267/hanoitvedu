/* main.js — progressive enhancement only.
   Every feature here degrades to a working server-rendered page when JS is off:
   the nav sheet is visible by default, the quiz posts as a normal form. */

(function () {
  "use strict";

  /* ---------------------------------------------------------------- nav */

  function initNav() {
    var toggle = document.getElementById("nav-toggle");
    var links = document.getElementById("nav-links");
    if (!toggle || !links) return;

    var mobile = window.matchMedia("(max-width: 900px)");

    function collapse(hide) {
      links.hidden = hide;
      toggle.setAttribute("aria-expanded", String(!hide));
    }

    // Only hide the sheet once we know JS is running, so a no-JS page keeps
    // the links visible.
    function sync() {
      if (mobile.matches) {
        collapse(true);
      } else {
        links.hidden = false;
        toggle.setAttribute("aria-expanded", "false");
      }
    }

    sync();
    mobile.addEventListener("change", sync);

    toggle.addEventListener("click", function () {
      collapse(!links.hidden);
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && mobile.matches && !links.hidden) {
        collapse(true);
        toggle.focus();
      }
    });
  }

  /* --------------------------------------------------------------- quiz */

  function clearMarks(form) {
    form.querySelectorAll(".quiz-option").forEach(function (option) {
      option.classList.remove("quiz-option--correct", "quiz-option--incorrect");
      var mark = option.querySelector(".quiz-option__mark");
      if (mark) mark.textContent = "";
    });
  }

  function markIcon(kind) {
    // Mirrors macros/icons.html icon_check / icon_cross.
    var colour = kind === "correct" ? "green" : "red";
    var path =
      kind === "correct" ? "M4 12.5l5 5L20 6.5" : "M6 6l12 12M18 6L6 18";
    return (
      '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" ' +
      'stroke="var(--c-' +
      colour +
      ')" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" ' +
      'class="icon" aria-hidden="true" focusable="false"><path d="' +
      path +
      '" /></svg>'
    );
  }

  function applyResults(form, payload) {
    clearMarks(form);

    Object.keys(payload.results).forEach(function (questionId) {
      var result = payload.results[questionId];
      var question = form.querySelector('[data-question="' + questionId + '"]');
      if (!question) return;

      question.querySelectorAll(".quiz-option").forEach(function (option) {
        var key = option.getAttribute("data-option");
        var mark = option.querySelector(".quiz-option__mark");
        if (key === result.answer) {
          option.classList.add("quiz-option--correct");
          if (mark) mark.innerHTML = markIcon("correct");
        } else if (key === result.chosen && !result.correct) {
          option.classList.add("quiz-option--incorrect");
          if (mark) mark.innerHTML = markIcon("incorrect");
        }
      });
    });

    var score = form.querySelector("[data-quiz-score]");
    if (score) {
      score.textContent = payload.score + " / " + payload.total;
      score.hidden = false;
    }
  }

  function initQuiz() {
    var form = document.querySelector("form[data-quiz]");
    if (!form || !window.fetch) return;

    var checkUrl = form.getAttribute("data-check-url");
    if (!checkUrl) return;

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      fetch(checkUrl, {
        method: "POST",
        body: new FormData(form),
        credentials: "same-origin",
        headers: { "X-Requested-With": "fetch" },
      })
        .then(function (response) {
          if (!response.ok) throw new Error(String(response.status));
          return response.json();
        })
        .then(function (payload) {
          applyResults(form, payload);
        })
        .catch(function () {
          // Grading is authoritative on the server; fall back to a real post.
          form.submit();
        });
    });
  }

  /* ------------------------------------------------------------ composer */

  function initComposer() {
    var textarea = document.querySelector(".composer__textarea");
    if (!textarea) return;

    function grow() {
      textarea.style.height = "auto";
      textarea.style.height = textarea.scrollHeight + "px";
    }
    textarea.addEventListener("input", grow);
  }

  /* ------------------------------------------------------- copy a prompt */

  function initCopyButtons() {
    var buttons = document.querySelectorAll("[data-copy]");
    if (!buttons.length || !navigator.clipboard) return;

    buttons.forEach(function (button) {
      var source = document.getElementById(button.getAttribute("data-copy"));
      if (!source) return;

      button.hidden = false;
      button.addEventListener("click", function () {
        navigator.clipboard.writeText(source.textContent.trim()).then(
          function () {
            button.setAttribute("data-copied", "true");
            window.setTimeout(function () {
              button.removeAttribute("data-copied");
            }, 1600);
          },
          function () {
            /* Clipboard denied: the prompt is still on screen to select. */
          }
        );
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initNav();
    initQuiz();
    initComposer();
    initCopyButtons();
  });
})();

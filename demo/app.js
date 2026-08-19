(() => {
  "use strict";

  const data = window.HSADL_DEMO;
  if (!data || !Array.isArray(data.cases)) {
    document.body.innerHTML = "<p>Case data could not be loaded.</p>";
    return;
  }

  const routeOrder = ["descriptive", "diagnostic", "predictive", "prescriptive", "decision"];
  const routeLabels = { diagnostic: "diagnostic / inferential" };
  const state = { route: "all", capability: "all", query: "" };
  const grid = document.querySelector("#case-grid");
  const emptyState = document.querySelector("#empty-state");
  const count = document.querySelector("#result-count");
  const search = document.querySelector("#case-search");
  const capabilitySelect = document.querySelector("#capability-filter");
  const routeFilters = document.querySelector("#route-filters");
  const dialog = document.querySelector("#case-dialog");
  const dialogContent = document.querySelector("#dialog-content");

  const escapeHtml = (value) => String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

  const normalizedRoutes = (item) => item.routes;
  const allRoutes = [...new Set(data.cases.flatMap(normalizedRoutes))]
    .sort((a, b) => routeOrder.indexOf(a) - routeOrder.indexOf(b));

  const routeButton = (route, label) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "filter-button";
    button.dataset.route = route;
    button.textContent = label;
    button.setAttribute("aria-pressed", route === state.route ? "true" : "false");
    button.addEventListener("click", () => {
      state.route = route;
      routeFilters.querySelectorAll("button").forEach((item) => {
        item.setAttribute("aria-pressed", item.dataset.route === route ? "true" : "false");
      });
      render();
    });
    return button;
  };

  routeFilters.append(routeButton("all", "All"));
  allRoutes.forEach((route) => routeFilters.append(routeButton(route, routeLabels[route] || route)));
  data.capabilities.forEach((capability) => {
    const option = document.createElement("option");
    option.value = capability.id;
    option.textContent = capability.label;
    capabilitySelect.append(option);
  });

  const matches = (item) => {
    const routeMatch = state.route === "all" || normalizedRoutes(item).includes(state.route);
    const capabilityMatch = state.capability === "all" || item.capabilities.includes(state.capability);
    const haystack = [
      item.title,
      item.domain,
      item.question,
      item.result,
      item.endpoint,
      item.boundary,
      ...item.capability_labels,
      ...item.signals,
    ].join(" ").toLocaleLowerCase();
    return routeMatch && capabilityMatch && haystack.includes(state.query);
  };

  const card = (item) => {
    const article = document.createElement("article");
    article.className = "case-card";
    article.innerHTML = `
      <div class="case-visual">
        <span class="case-number">${escapeHtml(item.number)}</span>
        <img src="${escapeHtml(item.figure)}" alt="${escapeHtml(item.figure_alt)}" loading="lazy">
      </div>
      <div class="case-body">
        <div class="case-kicker"><span>${escapeHtml(item.domain)}</span><span>${escapeHtml(normalizedRoutes(item).join(" · "))}</span></div>
        <h3>${escapeHtml(item.title)}</h3>
        <p class="case-question">${escapeHtml(item.question)}</p>
        <div class="tag-row">${item.signals.slice(0, 3).map((signal) => `<span class="tag">${escapeHtml(signal)}</span>`).join("")}</div>
        <p class="endpoint"><span>Valid endpoint</span><br>${escapeHtml(item.endpoint)}</p>
        <button class="card-action" type="button">Inspect evidence →</button>
      </div>`;
    article.querySelector("button").addEventListener("click", () => openCase(item));
    return article;
  };

  const openCase = (item) => {
    dialogContent.innerHTML = `
      <div class="dialog-figure"><img src="${escapeHtml(item.figure)}" alt="${escapeHtml(item.figure_alt)}"></div>
      <div class="dialog-body">
        <p class="eyebrow dark">Case ${escapeHtml(item.number)} · ${escapeHtml(item.domain)}</p>
        <h2 id="dialog-title">${escapeHtml(item.title)}</h2>
        <p class="dialog-question">${escapeHtml(item.question)}</p>
        <div class="tag-row">${item.capability_labels.map((label) => `<span class="tag">${escapeHtml(label)}</span>`).join("")}</div>
        <div class="dialog-grid">
          <div class="dialog-panel"><span>Supported result</span><p>${escapeHtml(item.result)}</p></div>
          <div class="dialog-panel"><span>Valid endpoint</span><p>${escapeHtml(item.endpoint)}</p></div>
          <div class="dialog-panel"><span>Claim boundary</span><p>${escapeHtml(item.boundary)}</p></div>
          <div class="dialog-panel"><span>Reviewer signals</span><p>${escapeHtml(item.signals.join(" · "))}</p></div>
        </div>
        <div class="dialog-links">
          <a href="${escapeHtml(item.case_card)}">Read case card</a>
          <a href="${escapeHtml(item.project)}">Open reproducible project</a>
        </div>
      </div>`;
    dialog.showModal();
  };

  const render = () => {
    const visible = data.cases.filter(matches);
    grid.replaceChildren(...visible.map(card));
    count.textContent = `${visible.length} ${visible.length === 1 ? "case" : "cases"}`;
    emptyState.hidden = visible.length !== 0;
  };

  search.addEventListener("input", () => {
    state.query = search.value.trim().toLocaleLowerCase();
    render();
  });
  capabilitySelect.addEventListener("change", () => {
    state.capability = capabilitySelect.value;
    render();
  });
  document.querySelector("#reset-filters").addEventListener("click", () => {
    state.route = "all";
    state.capability = "all";
    state.query = "";
    search.value = "";
    capabilitySelect.value = "all";
    routeFilters.querySelectorAll("button").forEach((item) => {
      item.setAttribute("aria-pressed", item.dataset.route === "all" ? "true" : "false");
    });
    render();
  });
  document.querySelector(".dialog-close").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });

  document.querySelector("#metric-cases").textContent = String(data.metrics.cases).padStart(2, "0");
  document.querySelector("#metric-routes").textContent = String(data.metrics.routes).padStart(2, "0");
  document.querySelector("#metric-capabilities").textContent = String(data.metrics.capabilities).padStart(2, "0");
  document.querySelector("#metric-figures").textContent = String(data.metrics.accessible_figures);
  document.querySelector("#portfolio-boundary").textContent = data.boundary;
  render();
})();

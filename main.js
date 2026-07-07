const panel = document.getElementById("content-panel");
const hitAreas = document.querySelectorAll(".level-hit");

function renderLayer(level) {
  const data = LAYERS[level];
  if (!data) return;

  let html = `<article class="layer-content" style="--accent: ${data.color}">`;
  html += `<h2>${data.title}</h2>`;

  if (data.items) {
    html += "<ul class='layer-list'>";
    for (const item of data.items) {
      html += `<li>${item}</li>`;
    }
    html += "</ul>";
  }

  if (data.sections) {
    for (const section of data.sections) {
      if (section.heading) {
        html += `<h3>${section.heading}</h3>`;
      }
      if (section.bullets) {
        html += "<ul>";
        for (const bullet of section.bullets) {
          html += `<li>${bullet}</li>`;
        }
        html += "</ul>";
      }
    }
  }

  html += "</article>";
  panel.innerHTML = html;
  panel.scrollTop = 0;
}

function setActiveLevel(level) {
  hitAreas.forEach((area) => {
    area.classList.toggle("active", area.dataset.level === level);
  });

  renderLayer(level);
}

hitAreas.forEach((area) => {
  area.addEventListener("click", () => setActiveLevel(area.dataset.level));
  area.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      setActiveLevel(area.dataset.level);
    }
  });
  area.setAttribute("tabindex", "0");
  area.setAttribute("role", "button");
});

setActiveLevel("1");

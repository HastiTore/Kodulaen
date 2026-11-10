// Annuity calculator. Runs in the browser only: nothing is sent anywhere.
(function () {
  var form = document.getElementById("calc");
  var out = document.getElementById("calc-out");
  if (!form || !out) return;

  var euribor = parseFloat(form.getAttribute("data-euribor"));
  var average = parseFloat(form.getAttribute("data-average"));
  var lang = form.getAttribute("data-lang") || "et";
  var labels = {
    et: {
      rate: "Intress kokku",
      payment: "Kuumakse",
      total: "Kokku tagasi maksta",
      interest: "Intressikulu",
      compare: "Sama laen Eesti Panga keskmise intressiga ({rate})",
      perMonth: "kuus"
    },
    en: {
      rate: "Total rate",
      payment: "Monthly payment",
      total: "Total repaid",
      interest: "Interest paid",
      compare: "The same loan at Eesti Pank’s average rate ({rate})",
      perMonth: "a month"
    }
  }[lang] || {};

  function money(value) {
    var rounded = Math.round(value * 100) / 100;
    var parts = rounded.toFixed(2).split(".");
    var whole = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, lang === "et" ? "\u00a0" : ",");
    if (lang === "et") return whole + "," + parts[1] + "\u00a0€";
    return "€" + whole + "." + parts[1];
  }

  function percent(value) {
    var text = value.toFixed(3).replace(/0+$/, "").replace(/\.$/, "");
    if (text.indexOf(".") === -1) text += lang === "et" ? ",00" : ".00";
    return (lang === "et" ? text.replace(".", ",") : text) + "%";
  }

  function payment(principal, annualPct, months) {
    var r = annualPct / 100 / 12;
    if (r === 0) return principal / months;
    var factor = Math.pow(1 + r, months);
    return (principal * r * factor) / (factor - 1);
  }

  function read(id, fallback, min, max) {
    var node = document.getElementById(id);
    var value = node ? parseFloat(String(node.value).replace(",", ".")) : NaN;
    if (!isFinite(value)) value = fallback;
    // Clamp only the number used in the arithmetic. The field keeps what the
    // person typed, so a partly typed figure is not overwritten mid-keystroke.
    return Math.min(max, Math.max(min, value));
  }

  function render() {
    var amount = read("calc-amount", 100000, 1000, 1000000);
    var years = read("calc-term", 25, 1, 30);
    var margin = read("calc-margin", 1.5, 0, 10);
    var months = Math.round(years * 12);
    var rate = euribor + margin;
    var monthly = payment(amount, rate, months);
    var total = monthly * months;
    var interest = total - amount;
    var averageMonthly = payment(amount, average, months);

    var rows = [
      [labels.rate, percent(rate)],
      [labels.payment, money(monthly)],
      [labels.total, money(total)],
      [labels.interest, money(interest)]
    ];

    var html = '<dl class="calc-result">';
    rows.forEach(function (row) {
      html += "<div><dt>" + row[0] + "</dt><dd>" + row[1] + "</dd></div>";
    });
    html += "</dl>";
    html +=
      '<p class="small">' +
      labels.compare.replace("{rate}", percent(average)) +
      ": <strong>" +
      money(averageMonthly) +
      "</strong> " +
      labels.perMonth +
      ".</p>";
    out.innerHTML = html;
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    render();
  });
  ["calc-amount", "calc-term", "calc-margin"].forEach(function (id) {
    var node = document.getElementById(id);
    if (node) node.addEventListener("input", render);
  });
  render();
})();

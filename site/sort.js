/* Reorders the comparison table. Default HTML order is alphabetical.
   Empty values stay last. Nothing is scored or highlighted. */
(function () {
  var keySel = document.getElementById("sort-key");
  var dirSel = document.getElementById("sort-dir");
  var table = document.getElementById("compare");
  var status = document.getElementById("sort-status");
  if (!keySel || !dirSel || !table || !table.tBodies[0]) return;
  var tbody = table.tBodies[0];
  var original = Array.prototype.slice.call(tbody.rows);
  var numeric = {
    "min-loan": true,
    down: true,
    ltv: true,
    "ltv-eis": true,
    term: true,
    nominal: true,
    apr: true
  };

  function apply() {
    var key = keySel.value;
    var dir = dirSel.value;
    var rows = original.slice();
    if (!(key === "bank" && dir === "asc")) {
      rows.sort(function (a, b) {
        var av = a.getAttribute("data-" + key) || "";
        var bv = b.getAttribute("data-" + key) || "";
        var aEmpty = av === "";
        var bEmpty = bv === "";
        if (aEmpty || bEmpty) {
          if (aEmpty && bEmpty) {
            return (a.getAttribute("data-bank") || "").localeCompare(b.getAttribute("data-bank") || "", "et");
          }
          return aEmpty ? 1 : -1;
        }
        var c;
        if (numeric[key]) c = Number(av) - Number(bv);
        else c = av.localeCompare(bv, "et", { numeric: true });
        if (c === 0) c = (a.getAttribute("data-bank") || "").localeCompare(b.getAttribute("data-bank") || "", "et");
        return dir === "desc" ? -c : c;
      });
    }
    rows.forEach(function (row) { tbody.appendChild(row); });
    if (status) {
      status.textContent = keySel.options[keySel.selectedIndex].text + ", " + dirSel.options[dirSel.selectedIndex].text;
    }
  }

  keySel.addEventListener("change", apply);
  dirSel.addEventListener("change", apply);
})();

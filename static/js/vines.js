/* The storefront's vine frame: twining vines with leaves, flowers, birds
   and insects around the page (.page-sheet[data-vines]), leafy branches
   between page areas (.vine-divider) and grass and ferns above the footer
   (.vine-ground).  Decoration only: every drawing is aria-hidden, the
   page reads the same without it, and without JS the dividers fall back
   to the plain vine border in site.css.

   The leaves and creatures are symbols in static/img/motifs.svg (orn-*);
   this script only places them.  A seeded random keeps the arrangement
   the same on every load, and it is redrawn when the page's size changes. */
(function () {
  "use strict";

  var NS = "http://www.w3.org/2000/svg";
  var LEAF_SPACING = 26;       // px between leaves along a vine, at full size
  var CREATURE_EVERY = 650;    // px between insects up the sides
  var FULL_GUTTER = 92;        // the gutter the drawings are sized for
  // Each symbol's viewBox (x, y, width, height), from motifs.svg.
  var BOX = {
    "leaf-a": [-1, -9, 32, 18], "leaf-b": [-1, -14, 33, 28], "leaf-c": [-1, -12, 28, 24],
    blossom: [-14, -14, 28, 28], berries: [-4, -4, 13, 14], bird: [-32, -34, 57, 36],
    butterfly: [-20, -22, 40, 40], bee: [-12, -15, 29, 21], dragonfly: [-27, -22, 39, 44],
    ladybird: [-7, -6, 16, 12], snail: [-17, -21, 38, 22], mushroom: [-11, -17, 22, 18], fern: [-12, -18, 24, 37]
  };
  var sprite = "";

  function el(tag, attrs, parent) {
    var e = document.createElementNS(NS, tag);
    Object.keys(attrs).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (parent) { parent.appendChild(e); }
    return e;
  }

  function seeded(seed) {
    return function () {
      seed = (seed + 0x6D2B79F5) | 0;
      var t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function place(g, name, x, y, rotate, scale, cls) {
    var b = BOX[name];
    return el("use", {
      href: sprite + "#orn-" + name, x: b[0], y: b[1], width: b[2], height: b[3],
      transform: "translate(" + x.toFixed(1) + " " + y.toFixed(1) + ") rotate(" + rotate.toFixed(1) + ") scale(" + scale.toFixed(3) + ")",
      "class": cls || ""
    }, g);
  }

  // Points along a gently waving line from start, in direction dir.
  function wave(start, dir, len, amp, wavelength, phase) {
    var n = [-dir[1], dir[0]], pts = [];
    for (var u = 0; u <= len; u += 3) {
      var k = Math.min(1, u / 50, (len - u) / 50);
      var off = amp * k * (Math.sin(2 * Math.PI * u / wavelength + phase) + 0.35 * Math.sin(2 * Math.PI * u / (wavelength * 2.3) + 2 * phase));
      pts.push([start[0] + dir[0] * u + n[0] * off, start[1] + dir[1] * u + n[1] * off]);
    }
    return pts;
  }

  function pathData(pts) {
    return "M" + pts.map(function (p) { return p[0].toFixed(1) + " " + p[1].toFixed(1); }).join("L");
  }

  function angleAt(pts, i) {
    var a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)];
    return Math.atan2(b[1] - a[1], b[0] - a[0]) * 180 / Math.PI;
  }

  function spiral(g, x, y, angle, radius, side, width) {
    var a0 = angle * Math.PI / 180;
    var cx = x - Math.sin(a0) * radius * side, cy = y + Math.cos(a0) * radius * side;
    var t0 = Math.atan2(y - cy, x - cx), pts = [];
    for (var t = 0; t <= 1.001; t += 0.04) {
      var th = t0 + side * t * 3.2 * Math.PI, r = radius * (1 - 0.8 * t);
      pts.push([cx + r * Math.cos(th), cy + r * Math.sin(th)]);
    }
    el("path", { d: pathData(pts), "class": "orn-tendril", "stroke-width": width }, g);
  }

  // One twining vine: a main stem and a thinner twin crossing it, with
  // leaves, tendrils, flowers and berries.  skip(x, y): leave that spot bare.
  function vine(g, start, dir, len, s, rand, skip) {
    var amp = 9 * s, wavelength = 150 * s;
    var main = wave(start, dir, len, amp, wavelength, rand() * 6);
    var twin = wave(start, dir, len, amp * 0.9, wavelength, Math.PI + rand() * 0.6);
    el("path", { d: pathData(twin), "class": "orn-vine-twin", "stroke-width": 1.8 * Math.max(s, 0.6) }, g);
    el("path", { d: pathData(main), "class": "orn-vine", "stroke-width": 3 * Math.max(s, 0.6) }, g);
    var step = Math.max(2, Math.round(LEAF_SPACING * Math.max(s, 0.55) / 3));
    var side = 1;
    for (var i = 4; i < main.length - 4; i += step + Math.floor(rand() * 3)) {
      var x = main[i][0], y = main[i][1];
      if (skip && skip(x, y)) { continue; }
      var shape = rand() < 0.6 ? "leaf-a" : (rand() < 0.5 ? "leaf-b" : "leaf-c");
      place(g, shape, x, y, angleAt(main, i) + side * (35 + rand() * 35), s * (0.65 + rand() * 0.45), "lv" + (1 + Math.floor(rand() * 3)));
      side = -side;
      var r = rand();
      if (r < 0.09) {
        place(g, "blossom", x + side * 9 * s, y - 9 * s, rand() * 60, s * 0.85);
      } else if (r < 0.15) {
        place(g, "berries", x - side * 6 * s, y + 7 * s, 0, s * 0.8);
      } else if (r < 0.26) {
        var j = Math.min(twin.length - 1, i + 2);
        spiral(g, twin[j][0], twin[j][1], angleAt(twin, j), 7 * s, side, 1.1);
      }
    }
    return main;
  }

  function cornerTuft(g, x, y, s, rand) {
    for (var k = 0; k < 7; k++) {
      place(g, k % 2 ? "leaf-a" : "leaf-c", x, y, k * 51 + rand() * 20, s * 1.1, "lv" + (1 + k % 3));
    }
    place(g, "blossom", x, y, rand() * 70, s * 1.4);
  }

  // Birds and snails stand upright on the vine; insects follow its line.
  function creature(g, name, pts, i, s) {
    var x = pts[i][0], y = pts[i][1];
    if (name === "bird" || name === "snail") {
      place(g, name, x, y + 2 * s, 0, s);
    } else {
      place(g, name, x, y, angleAt(pts, i) + (name === "butterfly" ? 90 : 0) - 15, s);
    }
  }

  function clear(node) {
    while (node.firstChild) { node.removeChild(node.firstChild); }
  }

  function drawFrame(sheet) {
    var svg = sheet.querySelector(":scope > svg.vine-frame");
    if (!svg) {
      svg = el("svg", { "class": "vine-frame", "aria-hidden": "true", focusable: "false" });
      sheet.insertBefore(svg, sheet.firstChild);
    }
    clear(svg);
    var W = sheet.offsetWidth, H = sheet.offsetHeight;
    var gutter = parseFloat(getComputedStyle(sheet).paddingLeft) || 0;
    if (!W || !H || gutter < 12) { return; }
    var s = gutter / FULL_GUTTER, c = gutter / 2, rand = seeded(7), g = el("g", {}, svg);
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    var top = vine(g, [c, c], [1, 0], W - 2 * c, s, rand);
    var bottom = vine(g, [c, H - c], [1, 0], W - 2 * c, s, rand);
    var left = vine(g, [c, c], [0, 1], H - 2 * c, s, rand);
    var right = vine(g, [W - c, c], [0, 1], H - 2 * c, s, rand);
    [[c, c], [W - c, c], [c, H - c], [W - c, H - c]].forEach(function (p) { cornerTuft(g, p[0], p[1], s, rand); });
    var cs = Math.max(s, 0.55);
    function at(pts, f) { return Math.floor(pts.length * f); }
    creature(g, "bird", top, at(top, 0.28), cs * 1.05);
    creature(g, "butterfly", top, at(top, 0.7), cs);
    creature(g, "snail", bottom, at(bottom, 0.2), cs);
    creature(g, "bird", bottom, at(bottom, 0.78), cs);
    var insects = ["butterfly", "bee", "ladybird", "dragonfly", "bee", "butterfly"];
    var every = Math.floor(CREATURE_EVERY / 3);
    [left, right].forEach(function (pts, side) {
      for (var i = Math.floor(every * (0.4 + side * 0.5)), k = side * 2; i < pts.length - 20; i += every, k++) {
        creature(g, insects[k % insects.length], pts, i, cs);
      }
    });
  }

  function drawDivider(div, index) {
    clear(div);
    var W = div.offsetWidth, H = div.offsetHeight;
    if (!W || !H) { return; }
    var s = H / 64, mid = W / 2, rand = seeded(index * 131 + 5);
    var svg = el("svg", { viewBox: "0 0 " + W + " " + H, "aria-hidden": "true", focusable: "false" }, div);
    var g = el("g", {}, svg), y0 = H / 2 + 6 * s;
    var pts = vine(g, [24, y0], [1, 0], W - 48, s * 0.9, rand, function (x) { return Math.abs(x - mid) < 34 * s; });
    spiral(g, 24, y0, 180, 9 * s, 1, 2.2);
    spiral(g, W - 24, y0, 0, 9 * s, -1, 2.2);
    var name = div.getAttribute("data-creature") || "bee";
    var p = pts[Math.floor(pts.length / 2)];
    if (name === "bird") {
      place(g, "bird", p[0], p[1] + 1, 0, s * 0.95);
    } else {
      place(g, "blossom", p[0], p[1], 0, s * 1.1);
      place(g, BOX[name] ? name : "bee", p[0] + 4, p[1] - 20 * s, name === "dragonfly" ? -10 : 0, s * 0.9);
    }
    div.classList.add("drawn");
  }

  function drawGround(div, index) {
    clear(div);
    var W = div.offsetWidth, H = div.offsetHeight;
    if (!W || !H) { return; }
    var rand = seeded(index * 71 + 3);
    var svg = el("svg", { viewBox: "0 0 " + W + " " + H, "aria-hidden": "true", focusable: "false" }, div);
    var d = "";
    for (var x = 4; x < W; x += 8 * (0.6 + rand())) {
      var h = 10 + rand() * 22, lean = (rand() - 0.5) * 14;
      d += "M" + x.toFixed(1) + " " + H + "Q" + (x + lean / 2).toFixed(1) + " " + (H - h / 2).toFixed(1) + " " + (x + lean).toFixed(1) + " " + (H - h).toFixed(1);
    }
    el("path", { d: d, "class": "orn-grass" }, svg);
    for (var fx = 40 + rand() * 60; fx < W - 30; fx += 110 + rand() * 160) {
      var r = rand();
      if (r < 0.35) {
        place(svg, "fern", fx, H - 18, (rand() - 0.5) * 20, 1.1);
      } else if (r < 0.6) {
        place(svg, "mushroom", fx, H, 0, 0.9 + rand() * 0.5);
      } else if (r < 0.75) {
        place(svg, "blossom", fx, H - 14 - rand() * 10, 0, 0.8);
      }
    }
    place(svg, "snail", W * 0.62, H, 0, 1);
  }

  function drawAll() {
    var sheet = document.querySelector(".page-sheet[data-vines]");
    if (!sheet) { return; }
    Array.prototype.forEach.call(document.querySelectorAll(".vine-divider"), drawDivider);
    Array.prototype.forEach.call(document.querySelectorAll(".vine-ground"), drawGround);
    drawFrame(sheet);   // last: dividers and ground can change the page's height
  }

  function start() {
    var sheet = document.querySelector(".page-sheet[data-vines]");
    if (!sheet) { return; }
    sprite = sheet.getAttribute("data-vines");
    drawAll();
    var lastWidth = sheet.offsetWidth, lastHeight = sheet.offsetHeight, timer = null;
    if (window.ResizeObserver) {
      new ResizeObserver(function () {
        if (sheet.offsetWidth === lastWidth && sheet.offsetHeight === lastHeight) { return; }
        lastWidth = sheet.offsetWidth;
        lastHeight = sheet.offsetHeight;
        clearTimeout(timer);
        timer = setTimeout(drawAll, 80);
      }).observe(sheet);
    }
    if (document.fonts && document.fonts.ready) { document.fonts.ready.then(drawAll); }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();

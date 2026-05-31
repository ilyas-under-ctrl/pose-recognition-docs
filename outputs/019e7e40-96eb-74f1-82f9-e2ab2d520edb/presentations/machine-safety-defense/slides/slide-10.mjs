import { base, body, C, fig, kicker, note, title } from "./common.mjs";

export async function slide10(presentation, ctx) {
  const slide = presentation.slides.add();
  base(slide, ctx, { footer: "Artefact à montrer: timing_budget.png" });
  kicker(slide, ctx, "Prudence déploiement", { color: C.red });
  title(slide, ctx, "Le prototype reste 2D et doit encore prouver toute la chaîne d'arrêt.", { w: 980 });
  await ctx.addImage(slide, { path: fig("timing_budget.png"), x: 700, y: 128, w: 500, h: 360, fit: "contain", alt: "Timing budget" });
  ctx.addShape(slide, { x: 72, y: 176, w: 540, h: 320, fill: C.white, line: ctx.line(C.red, 2) });
  body(slide, ctx, "Pourquoi le prototype reste limité", { x: 100, y: 206, w: 360, h: 30, size: 26, bold: true, color: C.red });
  body(slide, ctx, "Zone dangereuse projetée en 2D\nCaméra et machine fixes\nDeux acteurs seulement\nPas encore de mesure complète caméra -> arrêt mécanique", {
    x: 100,
    y: 258,
    w: 420,
    h: 176,
    size: 20,
  });
  note(slide, ctx, "La projection 2D est acceptable pour ce prototype à caméra fixe. Pour un déploiement, il faudra une validation 3D plus robuste, avec multi-angle ou profondeur, plus une mesure complète de la latence jusqu'à l'action mécanique.", {
    x: 92,
    y: 534,
    w: 1112,
    h: 62,
    fill: C.redSoft,
    line: C.red,
    size: 17,
  });
  return slide;
}
